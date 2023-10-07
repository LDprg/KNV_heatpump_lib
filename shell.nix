{ nixpkgs ? import <nixpkgs> { } }:
with nixpkgs;
mkShellNoCC { nativeBuildInputs = [ python3 ]; }
