set -ex

if [[ ${cuda_compiler_version} != "None" ]]; then
   export ENABLE_CUDA=1
else
   export ENABLE_CUDA=0
fi

# Workaround for https://github.com/conda-forge/conda-forge.github.io/issues/1880
export PKG_CONFIG=$BUILD_PREFIX/bin/pkgconf

# We explicitly depend on lgpl's variant of ffmpeg in the recipe.yaml to ensure that
# we do not have license violation due to linking a GPL project
export I_CONFIRM_THIS_IS_NOT_A_LICENSE_VIOLATION=1

export TORCHCODEC_DISABLE_COMPILE_WARNING_AS_ERROR=ON

# Use Ninja generator for consistency with Windows
export CMAKE_GENERATOR=Ninja

pip install . --no-deps --no-build-isolation -vv

# Remove spurious files created by gtk post-link activation script,
# that should not be included as part of the installed files
rm -f $PREFIX/lib/gdk-pixbuf-2.0/*/loaders.cache
