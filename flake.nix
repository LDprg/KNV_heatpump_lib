{
  outputs = { nixpkgs }: {
    devShell.${builtins.currentSystem} =
      import ./shell.nix { inherit nixpkgs };
  };
}