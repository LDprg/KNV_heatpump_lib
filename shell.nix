{ system ? builtins.currentSystem, pkgs ? import <nixpkgs> { inherit system; }
}:
pkgs.mkShell {
  nativeBuildInputs = with pkgs;
    [
      (python3.withPackages
        (ps: with ps; [ pip wheel setuptools setuptools-scm build pytest pytest-asyncio websockets async-timeout ]))
    ];
}
