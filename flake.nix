{
  description = "ha-prometheus-sensor";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    git-hooks.url = "github:cachix/git-hooks.nix";
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
        in
        {
          checks = {
            pre-commit = git-hooks.lib.${system}.run {
              src = ./.;
              hooks = {
                isort.enable = true;
                ruff.enable = true;
                ruff-format = {
                  enable = true;
                  entry = "${pkgs.ruff}/bin/ruff format";
                  pass_filenames = false;
                };
              };
            };
          };
          devShells.default =
            with pkgs;
            mkShell {
              inherit (self.checks.${system}.pre-commit) shellHook;

              buildInputs =
                [
                  isort
                  pyright
                  ruff
                ]
                ++ (with python312.pkgs; [
                  aiohttp
                  (toPythonModule pkgs.home-assistant)
                  voluptuous
                ]);
            };

          formatter = pkgs.nixfmt-rfc-style;
        }
      );
}
