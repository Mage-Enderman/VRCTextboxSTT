@echo off
cd %~dp0

if exist build rmdir /S /Q build
mkdir build\TextboxSTT

echo Building launcher executables...
dotnet publish TextboxSTT_Launcher\TextboxSTT_Launcher.sln -c Release -r win-x64

copy /Y TextboxSTT_Launcher\TextboxSTT_Launcher\bin\Release\net4.8.1\win-x64\publish\TextboxSTT_Launcher.exe build\TextboxSTT\TextboxSTT.exe
copy /Y TextboxSTT_Launcher\obs_only_Launcher\bin\Release\net4.8.1\win-x64\publish\obs_only_Launcher.exe build\TextboxSTT\obs_only.exe
copy /Y TextboxSTT_Launcher\VRCaptions_Launcher\bin\Release\net4.8.1\win-x64\publish\VRCaptions_Launcher.exe build\TextboxSTT\VRCaptions.exe

echo Copying source and assets...
robocopy src build\TextboxSTT\src /E /NFL /NDL /NJH /NJS /nc /ns /np
if exist README.md copy /Y README.md build\TextboxSTT\
if exist LICENSE copy /Y LICENSE build\TextboxSTT\

echo Extracting bundled Python environment...
7z x git_python.7z -obuild\TextboxSTT -y

echo Upgrading pip...
build\TextboxSTT\python\python.exe -m pip install --upgrade pip

if exist build\TextboxSTT\python\cache rmdir /S /Q build\TextboxSTT\python\cache

echo Packaging TextboxSTT.zip...
cd build
7z a -tzip -mx=7 TextboxSTT.zip TextboxSTT
cd ..

echo Build completed: build\TextboxSTT.zip