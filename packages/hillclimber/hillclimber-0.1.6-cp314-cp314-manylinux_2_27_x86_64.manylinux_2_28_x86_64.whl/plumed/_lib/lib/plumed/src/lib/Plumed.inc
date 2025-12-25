PLUMED_RUNTIME_LOAD= "/project/src/plumed/_lib/lib/libplumedWrapper.a" -ldl  
PLUMED_STATIC_LOAD= "/project/src/plumed/_lib/lib/libplumed.a" -ldl  -lstdc++ -lz -ldl  -Wl,-rpath,RIGIN/../lib -rdynamic -Wl,-Bsymbolic -fopenmp 
PLUMED_SHARED_LOAD= "/project/src/plumed/_lib/lib/libplumed.so" -ldl  
PLUMED_RUNTIME_DEPENDENCIES=
PLUMED_STATIC_DEPENDENCIES= "/project/src/plumed/_lib/lib/libplumed.a"
PLUMED_SHARED_DEPENDENCIES= "/project/src/plumed/_lib/lib/libplumed.so"
PLUMED_FORTRAN= "/project/src/plumed/_lib/lib/plumed/fortran/plumed.f90"
PLUMED_FORTRAN08= "/project/src/plumed/_lib/lib/plumed/fortran/plumed_f08.f90"
