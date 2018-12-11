BASIS
{{ basis }}


Atomtypes=2 Charge={{ charge }} {{ sym_str }} Angstrom
{% for charge, atom_num, elem_coords in atoms_data %}
Charge={{ "%.1f" % charge }} Atoms={{ atom_num }}
{% for atom, (x, y, z) in elem_coords %}
{{ atom }} {{ "%.8f" % x }} {{ "%.8f" % y }} {{ "%.8f" % z }}
{% endfor %}
{% endfor %}
