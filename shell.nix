{ system ? builtins.currentSystem, pkgs ? import <nixpkgs> { inherit system; }
}:
pkgs.mkShell { nativeBuildInputs = with pkgs; [ python3 ]; }
