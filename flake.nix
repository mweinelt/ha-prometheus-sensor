{
  description = "ha-prometheus-sensor";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    git-hooks = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      git-hooks,
      flake-utils,
    }:

    flake-utils.lib.eachSystem
      [
        "aarch64-linux"
        "x86_64-linux"
      ]
      (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          lib = pkgs.lib;

          pythonEnv = pkgs.home-assistant.python.withPackages (
            ps: with ps; [
              aiohttp
              (toPythonModule pkgs.home-assistant)
              voluptuous
            ]
          );
        in
        {
          checks = {
            pre-commit = git-hooks.lib.${system}.run {
              src = ./.;
              hooks = {
                ruff.enable = true;
                ruff-format.enable = true;
                pyright = {
                  enable = true;
                  entry = "${lib.getExe pkgs.pyright} --pythonpath ${pythonEnv.interpreter}";
                };
              };
            };
          };
          devShells.default =
            with pkgs;
            mkShell {
              inherit (self.checks.${system}.pre-commit) shellHook;

              buildInputs = [ pythonEnv ] ++ self.checks.${system}.pre-commit.enabledPackages;
            };

          formatter = pkgs.nixfmt-rfc-style;
        }
      );
}
