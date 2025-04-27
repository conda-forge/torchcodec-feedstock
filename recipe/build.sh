set -ex

if [[ ${cuda_compiler_version} != "None" ]]; then
   export ENABLE_CUDA=1
else
   export ENABLE_CUDA=0
fi

# Also run C++ tests
mkdir build_cxx_tests
cd build_cxx_tests
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=1 $CMAKE_ARGS ..
cmake --build . -- VERBOSE=1
if [[ "${CONDA_BUILD_CROSS_COMPILATION:-}" != "1" || "${CROSSCOMPILING_EMULATOR}" != "" ]]; then
ctest --rerun-failed --output-on-failure
fi
cd ..

# We explicitly depend on lgpl's variant of ffmpeg in the recipe.yaml to ensure that
# we do not have license violation due to linking a GPL project
export I_CONFIRM_THIS_IS_NOT_A_LICENSE_VIOLATION=1

pip install . --no-deps --no-build-isolation -vv

# Remove spurious files created by gtk post-link activation script,
# that should not be included as part of the installed files
rm -f $PREFIX/lib/gdk-pixbuf-2.0/*/loaders.cache
