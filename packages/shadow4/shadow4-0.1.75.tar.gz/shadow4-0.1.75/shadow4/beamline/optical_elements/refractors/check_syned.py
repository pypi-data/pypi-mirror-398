from syned.beamline.optical_elements.refractors.lens import Lens

a = Lens()

print(a.get_surface_shape(index=0))
print(a.get_surface_shape(index=1))

print(a.get_surface_shape1())
print(a.get_surface_shape2())