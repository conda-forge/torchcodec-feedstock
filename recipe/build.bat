if not "%cuda_compiler_version%" == "None" (
    set ENABLE_CUDA=1
) else (
    set ENABLE_CUDA=0
)

:: Workaround for https://github.com/conda-forge/conda-forge.github.io/issues/1880
set PKG_CONFIG=%BUILD_PREFIX%\Library\bin\pkgconf.exe

:: We explicitly depend on lgpl's variant of ffmpeg in the recipe.yaml to ensure that
:: we do not have license violation due to linking a GPL project
set I_CONFIRM_THIS_IS_NOT_A_LICENSE_VIOLATION=1

set TORCHCODEC_DISABLE_COMPILE_WARNING_AS_ERROR=ON

:: Use Ninja generator as it is more robust to CUDA-related CMake issues
set "CMAKE_GENERATOR=Ninja"
:: Ensure that env variables not supported by Ninja are not set
set "CMAKE_GENERATOR_PLATFORM="
set "CMAKE_GENERATOR_TOOLSET="

pip install . --no-deps --no-build-isolation -vv
if %ERRORLEVEL% neq 0 exit 1
