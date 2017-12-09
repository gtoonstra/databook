to_remove = 'Entity'
mid_types = ['Database','Tableau', 'Org']


def discover_type(labels):
    labels.remove(to_remove)
    for midtype in mid_types:
        if midtype in labels:
            break
    labels.remove(midtype)
    end_type = midtype + ":" + labels[0]
    return end_type
