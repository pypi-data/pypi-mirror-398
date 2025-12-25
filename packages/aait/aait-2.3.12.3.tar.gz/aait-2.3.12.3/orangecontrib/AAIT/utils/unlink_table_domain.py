from Orange.data import Table, Domain, Instance


def unlink_domain(table: Table) -> Table:
    dom = table.domain

    # Recrée les variables sans compute_value
    new_attrs  = [v.copy(compute_value=None) for v in dom.attributes]
    new_cls    = [v.copy(compute_value=None) for v in dom.class_vars]
    new_metas  = [v.copy(compute_value=None) for v in dom.metas]
    new_domain = Domain(new_attrs, new_cls, new_metas)

    instances = []
    for row in table:
        # on évalue toutes les valeurs ici (les compute_value sont calculés)
        attr_vals = [row[v] for v in dom.attributes]
        cls_vals  = [row[v] for v in dom.class_vars]
        inst = Instance(new_domain, attr_vals + cls_vals)

        # on renseigne les métas via l’indexation
        for old_m, new_m in zip(dom.metas, new_metas):
            inst[new_m] = row[old_m]

        instances.append(inst)

    return Table.from_list(new_domain, instances)