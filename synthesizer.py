import re
import uuid
from typing import List, Dict, Any, Tuple
from models import Ingredient, Recipe

class Synthesizer:
    CANONICAL_NAMES = {
        'curd': 'yogurt',
        'dahi': 'yogurt',
        'yoghurt': 'yogurt',
        'yogurt': 'yogurt',
    }

    PHASE_KEYWORDS = {
        'prep': ['chop', 'slice', 'dice', 'peel', 'grate', 'measure', 'prepare', 'trim', 'wash', 'soak'],
        'mix': ['mix', 'whisk', 'combine', 'stir', 'fold', 'beat', 'blend', 'whip'],
        'rest': ['rest', 'let sit', 'prove', 'proof', 'stand', 'marinate'],
        'cook': ['steam', 'bake', 'fry', 'saute', 'simmer', 'cook', 'boil', 'roast', 'grill', 'heat', 'pressure'],
        'finish': ['garnish', 'serve', 'drizzle', 'sprinkle', 'plate']
    }

    @staticmethod
    def _normalize_step_text(s: str) -> str:
        return ' '.join(s.strip().split())

    @classmethod
    def canonical_name(cls, name: str) -> str:
        k = name.strip().lower()
        if k.endswith('s') and k[:-1] in cls.CANONICAL_NAMES:
            k = k[:-1]
        return cls.CANONICAL_NAMES.get(k, name.strip())

    # (batter / hints etc kept identical to your version) ...
    BATTER_KEYWORDS = [
        r"\bwhisk\b", r"\bmix\b", r"\bstir\b", r"\bcombine\b", r"\bfold\b",
        r"\badd\b", r"\bblend\b", r"\bgrind\b", r"\bmake.*batter\b",
    ]

    BATTER_INGREDIENT_HINTS = [
        "flour", "atta", "maida", "besan", "gram flour", "rice flour",
        "yogurt", "curd", "buttermilk", "milk", "water", "eggs",
        "semolina", "suji", "cornflour",
    ]

    LEAVENING_HINTS = [
        "eno", "baking soda", "baking powder", "yeast",
    ]

    COOKING_FINALIZATION_HINTS = [
        "steam", "fry", "bake", "rest", "ferment",
    ]

    @staticmethod
    def is_batter_step(step: str) -> bool:
        s = step.lower()
        if "batter" in s:
            return True
        if any(k in s for k in Synthesizer.BATTER_INGREDIENT_HINTS):
            if any(v in s for v in ["mix", "combine", "whisk", "blend", "stir", "make"]):
                return True
        if any(re.search(k, s) for k in Synthesizer.BATTER_KEYWORDS):
            return True
        return False

    @staticmethod
    def normalize_batter_steps(steps: List[str]) -> List[str]:
        batter_steps = [s for s in steps if Synthesizer.is_batter_step(s)]
        if not batter_steps:
            return steps
        combined = " ".join(batter_steps).lower()
        output = []
        if any(f in combined for f in ["flour", "gram", "rice", "maida", "semolina", "suji"]):
            output.append("Whisk the flour and liquids together, adding water gradually to form a smooth batter.")
        if any(k in combined for k in Synthesizer.LEAVENING_HINTS):
            output.append("Add the leavening agent (Eno, baking soda, or similar).")
        if "sugar" in combined or "salt" in combined or "spice" in combined:
            output.append("Add sugar, salt, and spices as required.")
        output.append("Mix gently until just combined.")
        final = []
        if any(k in combined for k in ["steam"]):
            final.append("Steam for 15 minutes.")
        elif any(k in combined for k in ["fry"]):
            final.append("Fry until golden.")
        elif any(k in combined for k in ["bake"]):
            final.append("Bake as required.")
        elif any(k in combined for k in ["rest", "ferment"]):
            final.append("Allow the batter to rest or ferment as required.")
        output.extend(final)
        return output

    # -------------------- NEW HELPER: generate prep from ingredients --------------------
    def generate_prep_from_ingredients(self, merged_ings: List[Ingredient]) -> List[str]:
        """
        Create deterministic prep sentences for staple ingredient patterns so that
        important ingredients (rice, urad dal, semolina, flour+yogurt) appear in steps.
        """
        names = {ing.name.strip().lower(): ing for ing in merged_ings}
        prep_lines: List[str] = []

        # IDLI / DOSA style: Rice + Urad Dal
        rice_keys = {'rice', 'idli rice', 'parboiled rice', 'idli rice (parboiled)'}
        urad_keys = {'urad dal', 'urad', 'black gram', 'black-gram'}

        has_rice = any(k in names for k in rice_keys)
        has_urad = any(k in names for k in urad_keys)

        if has_rice and has_urad:
            # conservative generic timings — safe guidance
            prep_lines.append("Soak rice and urad dal separately for 4–6 hours, then drain.")
            prep_lines.append("Grind soaked rice and urad dal to a smooth batter and combine; ferment if required.")
            return prep_lines

        # Semolina / Rava idli (quick)
        if 'semolina' in names or 'rava' in names:
            prep_lines.append("Mix semolina with yogurt and water to make a batter; let it rest for 10–15 minutes if using semolina.")
            return prep_lines

        # Batter base from flour + yogurt (e.g., quick dhokla/khaman)
        flour_aliases = {'gram flour', 'besan', 'maida', 'atta', 'flour'}
        yogurt_aliases = {'yogurt', 'curd', 'dahi', 'yoghurt'}
        has_flour = any(k in names for k in flour_aliases)
        has_yogurt = any(k in names for k in yogurt_aliases)
        if has_flour and has_yogurt:
            prep_lines.append("Whisk the flour and yogurt together, adding water gradually to form a smooth batter.")
            return prep_lines

        # default: nothing special
        return prep_lines
    # -------------------------------------------------------------------------------

    def merge_semantic_steps(self, steps: List[str]) -> List[str]:
        # simplified merger you already had (kept unchanged)
        norm_steps = []
        seen = set()
        for s in steps:
            if not s:
                continue
            s_norm = self._normalize_step_text(s)
            key = s_norm.lower()
            if key and key not in seen:
                seen.add(key)
                norm_steps.append(s_norm)
        if not norm_steps:
            return []
        flour_pattern = r"(gram flour|besan|semolina|suji|maida|atta|rice|[a-z ]+flour)"
        yogurt_pattern = r"(yogurt|curd|dahi|yoghurt)"
        batter_step = None
        for s in norm_steps:
            low = s.lower()
            if any(v in low for v in ["mix", "whisk", "combine", "stir"]):
                if re.search(flour_pattern, low) and re.search(yogurt_pattern, low):
                    m_flour = re.search(flour_pattern, low)
                    m_yog = re.search(yogurt_pattern, low)
                    flour_txt = (m_flour.group(1) if m_flour else "flour").strip()
                    yog_txt = (m_yog.group(1) if m_yog else "yogurt").strip()
                    flour_txt = flour_txt.title()
                    yog_txt = yog_txt.title()
                    batter_step = (
                        f"Whisk the {flour_txt} and {yog_txt} together, adding water gradually to form a smooth batter."
                    )
                    break
        key_add_names = ["water", "eno", "baking soda", "sugar", "salt"]
        seen_add = []
        for s in norm_steps:
            low = s.lower()
            if "add" in low:
                for name in key_add_names:
                    if name in low and name not in seen_add:
                        seen_add.append(name)
        add_step = None
        if seen_add:
            display_parts = []
            for n in seen_add:
                if n == "eno":
                    disp = "Eno"
                else:
                    disp = n
                display_parts.append(disp)
            if len(display_parts) == 1:
                list_txt = display_parts[0]
            else:
                list_txt = ", ".join(display_parts[:-1]) + " and " + display_parts[-1]
            add_step = f"Add {list_txt}. Mix gently until just combined."
        cook_step = None
        for s in norm_steps:
            low = s.lower()
            if "steam" in low:
                m_time = re.search(r"(\d+)\s*(?:mins?|minutes?)", low)
                if m_time:
                    cook_step = f"Steam for {m_time.group(1)} minutes."
                else:
                    cook_step = "Steam until cooked through."
                break
        if not cook_step:
            if any("steam" in s.lower() for s in norm_steps):
                cook_step = "Steam until cooked through."
        merged = []
        if batter_step:
            merged.append(self._normalize_step_text(batter_step))
        if add_step:
            merged.append(self._normalize_step_text(add_step))
        if cook_step:
            merged.append(self._normalize_step_text(cook_step))
        if not merged:
            return norm_steps
        return merged

    def remove_invalid_leavening_from_steps(self, steps: List[str], ingredients: List[Ingredient]) -> List[str]:
        has_eno = any(i.name.lower() == "eno" for i in ingredients)
        has_soda = any(i.name.lower() in ["baking soda", "soda"] for i in ingredients)
        if has_eno and not has_soda:
            cleaned = []
            for s in steps:
                s2 = s
                s2 = re.sub(r'\b(baking soda|soda)\b', '', s2, flags=re.I)
                s2 = re.sub(r'\band\s+and\b', 'and', s2, flags=re.I)
                s2 = re.sub(r'\b(and)\s*(?=[\.,;:])', '', s2, flags=re.I)
                s2 = re.sub(r'\band\s*$', '', s2, flags=re.I)
                s2 = re.sub(r'\s+', ' ', s2).strip()
                if s2:
                    cleaned.append(s2)
            return cleaned
        return steps

    def canonicalize_step_text(self, text: str) -> str:
        out = text
        for alias, canon in self.CANONICAL_NAMES.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            out = re.sub(pattern, canon.title(), out, flags=re.I)
        return out

    def normalize_leavening(self, ingredients: List[Ingredient]) -> List[Ingredient]:
        has_eno = any(i.name.lower() == "eno" for i in ingredients)
        has_soda = any(i.name.lower() in ["baking soda", "soda"] for i in ingredients)
        if has_eno and has_soda:
            ingredients = [i for i in ingredients if i.name.lower() not in ["baking soda", "soda"]]
        return ingredients

    def merge_ingredients(self, recipes: List[Recipe], requested_servings: int) -> List[Ingredient]:
        grouped: Dict[str, Dict[str, Any]] = {}
        for r in recipes:
            for ing in r.ingredients:
                cname = self.canonical_name(ing.name)
                key = cname.strip().lower()
                if key not in grouped:
                    grouped[key] = {"name": cname.strip(), "per_serving": [], "units": []}
                if r.servings <= 0:
                    raise ValueError("Source recipe has invalid servings")
                grouped[key]["per_serving"].append(ing.quantity / r.servings)
                grouped[key]["units"].append(ing.unit)
        merged: List[Ingredient] = []
        for key, data in grouped.items():
            avg_per_serving = sum(data["per_serving"]) / len(data["per_serving"])
            final_qty = round(avg_per_serving * requested_servings, 3)
            unit = max(set(data["units"]), key=data["units"].count) if data["units"] else ""
            merged.append(Ingredient(name=data["name"].title(), quantity=final_qty, unit=unit))
        merged = self.normalize_leavening(merged)
        return merged

    class FreeOpenLLM:
        """Adapter to call a local HuggingFace transformers pipeline for text2text-generation."""

        def __init__(self, model_name: str = 'lmsys/fastchat-t5-3b-v1.0'):
        #def __init__(self, model_name: str = 'google/gemma-2b'):
            self.model_name = model_name
            self._pipe = None
            try:
                from transformers import (
                    pipeline,
                    T5ForConditionalGeneration,
                    T5Tokenizer
                )

                tokenizer = T5Tokenizer.from_pretrained(model_name, use_fast=False)
                model = T5ForConditionalGeneration.from_pretrained(model_name)

                self._pipe = pipeline(
                    'text2text-generation',
                    model=model,
                    tokenizer=tokenizer,
                    device=-1
                )
            except Exception as e:
                self._pipe = None
                self._init_error = e

        def available(self) -> bool:
            return self._pipe is not None

        def generate(self, prompt: str, **gen_kwargs) -> str:
            if not self.available():
                raise RuntimeError(
                    f"LLM pipeline for {self.model_name} is not available. "
                    f"Init error: {getattr(self,'_init_error',None)}"
                )
            out = self._pipe(prompt, **gen_kwargs)
            if isinstance(out, list) and out:
                first = out[0]
                if isinstance(first, dict):
                    return first.get('generated_text', str(first))
                return str(first)
            return str(out)

    @classmethod
    def classify_phase(cls, step: str) -> str:
        low = step.lower()
        for phase in ['prep', 'mix', 'rest', 'cook', 'finish']:
            keywords = cls.PHASE_KEYWORDS.get(phase, [])
            for kw in keywords:
                if kw in low:
                    return phase
        if re.search(r'\b(min|minute|minutes|hr|hour|°c|°f|degrees|°)\b', low):
            return 'cook'
        return 'mix'

    def reorder_steps(self, steps: List[str]) -> List[str]:
        buckets: Dict[str, List[Tuple[int,str]]] = {'prep': [], 'mix': [], 'rest': [], 'cook': [], 'finish': []}
        for i, s in enumerate(steps):
            phase = self.classify_phase(s)
            buckets.setdefault(phase, []).append((i, s))

        ordered = []
        for phase in ['prep', 'mix', 'rest', 'cook', 'finish']:
            items = sorted(buckets.get(phase, []), key=lambda x: x[0])
            ordered.extend([s for _, s in items])
        return ordered if ordered else steps

    @staticmethod
    def has_time_or_temp(text: str) -> bool:
        return bool(re.search(
            r'\b(\d+\s?(mins?|minutes?|hrs?|hours?|°\s?[CF]|°C|°F|degrees))\b',
            text,
            flags=re.I
        ))

    def compute_ai_confidence(self, num_sources: int, steps: List[str], generated_text: str) -> float:
        base = 0.45
        src_bonus = min(0.25, 0.08 * num_sources)
        step_bonus = min(0.2, 0.02 * len(steps))
        time_bonus = 0.15 if any(self.has_time_or_temp(s) for s in steps) else 0.0
        length_penalty = 0.0
        if len(generated_text.split()) < 30:
            length_penalty = 0.1
        conf = base + src_bonus + step_bonus + time_bonus - length_penalty
        return round(max(0.0, min(0.99, conf)), 3)

    def synthesize(self, top_recipes: List[Recipe], requested_servings: int,
                   llm_model: str = 'lmsys/fastchat-t5-3b-v1.0', reorder: bool = True) -> Recipe:
        if not top_recipes:
            raise ValueError("No recipes provided for synthesis")

        # 1) merge ingredients first (so we can create prep lines referencing them)
        merged_ings = self.merge_ingredients(top_recipes, requested_servings)

        # 2) generate a deterministic prep block from merged ingredients
        prep_from_ings = self.generate_prep_from_ingredients(merged_ings)  # NEW: ensures rice/urad/semolina/batter bases are mentioned

        # 3) collect raw steps from sources
        raw_steps = []
        for r in top_recipes:
            for s in r.steps:
                s_norm = self._normalize_step_text(s)
                s_norm = self.canonicalize_step_text(s_norm)
                raw_steps.append(s_norm)

        # 4) prepend generated prep lines so merger/LLM will include them
        raw_steps = prep_from_ings + raw_steps

        # 5) build prompt / LLM path exactly as before (rest of synthesize logic unchanged)
        src = "\n".join(f"- {s}" for s in raw_steps)

        prompt = (
            f"Combine the following cooking actions into one clear, merged recipe for {requested_servings} servings.\n\n"
            f"Write 4–8 numbered steps. Keep steps short (one sentence each). Do NOT add new ingredients or quantities.\n"
            f"Try to include times/temperatures when they are present in the source actions.\n\n"
            f"Source actions:\n{src}\n\n"
            f"Output (begin with '1. '):\n1. "
        )

        llm = self.FreeOpenLLM(model_name=llm_model)
        if not llm.available():
            fallback_steps = []
            seen = set()
            for s in raw_steps:
                s_clean = re.sub(r'\s+', ' ', s).strip()
                if s_clean.lower() not in seen:
                    seen.add(s_clean.lower())
                    fallback_steps.append(s_clean)
            out_lines = fallback_steps[:6] if fallback_steps else ["Combine ingredients and cook as directed."]
            if reorder:
                out_lines = self.reorder_steps(out_lines)
            out_lines = self.merge_semantic_steps(out_lines)
            # clean leavening mentions if needed
            out_lines = self.remove_invalid_leavening_from_steps(out_lines, merged_ings)
            # --- Ensure generated prep lines (from merged ingredients) are present ---
            if prep_from_ings:
                prep_norm = [self._normalize_step_text(p) for p in prep_from_ings]
                # insert missing prep lines at start, preserving order (first prep_from_ings[0] first)
                for p in prep_norm[::-1]:  # insert in reverse so original order is preserved
                    if not any(p.lower() in s.lower() for s in out_lines):
                        out_lines.insert(0, p)
            # ------------------------------------------------------------------------
            generated_text = "\n".join(out_lines)
            ai_conf = self.compute_ai_confidence(len(top_recipes), out_lines, generated_text)
            validator_conf = round(min(1.0, ai_conf * 0.8), 3)
            title_base = top_recipes[0].title.split(':')[0].strip()
            title = f"Synthesized — {title_base} (for {requested_servings} servings)"
            meta = {
                "sources": [r.id for r in top_recipes],
                "ai_confidence": ai_conf,
                "synthesis_method": f"fallback:no-llm"
            }
            return Recipe(
                id=str(uuid.uuid4()),
                title=title,
                ingredients=merged_ings,
                steps=out_lines,
                servings=requested_servings,
                metadata=meta,
                validator_confidence=validator_conf,
                approved=True
            )

        gen_kwargs = {
            "max_new_tokens": 180,
            "do_sample": True,
            "temperature": 0.35,
            "top_p": 0.9,
        }

        generated = llm.generate(prompt, **gen_kwargs)

        pattern = r'^\s*(\d+)\.\s*(.+?)(?=\n\s*\d+\.|\Z)'
        matches = re.findall(pattern, generated, flags=re.S | re.M)

        out_lines = []
        for _, text in matches:
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)
            if not text.endswith(('.', '!', '?')):
                text = text + '.'
            if len(text.split()) >= 3:
                out_lines.append(text)

        if not out_lines:
            gen_clean = re.sub(r'\s+', ' ', generated).strip()
            sentences = re.split(r'(?<=[\.\?\!])\s+', gen_clean)
            short_sentences = [s.strip().rstrip('.') + '.' for s in sentences if len(s.split()) >= 3]
            out_lines = short_sentences[:8]

        if not out_lines:
            raise RuntimeError("Model failed to produce any usable steps.")

        out_lines = [' '.join(s.split()) for s in out_lines]
        out_lines = [self.canonicalize_step_text(s) for s in out_lines]

        if reorder:
            out_lines = self.reorder_steps(out_lines)
        out_lines = self.merge_semantic_steps(out_lines)
        out_lines = self.remove_invalid_leavening_from_steps(out_lines, merged_ings)
        # --- Ensure generated prep lines (from merged ingredients) are present ---
        if prep_from_ings:
            prep_norm = [self._normalize_step_text(p) for p in prep_from_ings]
            # insert missing prep lines at start, preserving order (first prep_from_ings[0] first)
            for p in prep_norm[::-1]:  # insert in reverse so original order is preserved
                if not any(p.lower() in s.lower() for s in out_lines):
                    out_lines.insert(0, p)
        # ------------------------------------------------------------------------

        generated_text = generated if isinstance(generated, str) else str(generated)
        ai_conf = self.compute_ai_confidence(len(top_recipes), out_lines, generated_text)
        validator_conf = round(min(1.0, ai_conf * 0.8), 3)

        base_title = top_recipes[0].title.split(':')[0].strip()
        title = f"Synthesized — {base_title} (for {requested_servings} servings)"

        meta = {
            "sources": [r.id for r in top_recipes],
            "ai_confidence": ai_conf,
            "synthesis_method": f"llm:{llm_model}"
        }

        merged_ings = self.normalize_leavening(merged_ings)

        return Recipe(
            id=str(uuid.uuid4()),
            title=title,
            ingredients=merged_ings,
            steps=out_lines,
            servings=requested_servings,
            metadata=meta,
            validator_confidence=validator_conf,
            approved=True
        )
