@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

set SPHINXBUILD=sphinx-build
set SOURCEDIR=source
set BUILDDIR=build

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have
	echo.Sphinx installed, then set the SPHINXBUILD environment variable to
	echo.point to the full path of the 'sphinx-build' executable. Alternatively
	echo you may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://sphinx-doc.org/
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %*
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %*

:end
popd

