
pragmas_to_lqp = {
    "rule_reasoner_sem_vo": "rel_primitive_force_faq_var_order",
    "rule_reasoner_phys_vo": "rel_primitive_force_var_order",
}

def pragma_to_lqp_name(name: str) -> str:
    if name in pragmas_to_lqp:
        return pragmas_to_lqp[name]
    else:
        # If we don't have a mapping for the built-in, we just pass it through as-is.
        return name
