{
  description = "KVN heatpump python libary";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, flake-utils }: {
    devShell.x86_64-linux =
      import ./shell.nix { nixpkgs = nixpkgs.legacyPackages.x86_64-linux; };
  };
}
