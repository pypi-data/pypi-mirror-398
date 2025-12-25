# code-owner: @agoose77
# This flake sets up an dev-shell that installs all the required
# packages for running deployer, and then installs the tool in the virtual environment
# It is not best-practice for the nix-way of distributing this code,
# but its purpose is to get an environment up and running.
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      inherit (pkgs) lib;

      python = pkgs.python313;
      node = pkgs.nodejs_22;
      packages =
        [
          python
          node
        ]
        ++ (with pkgs; [
          cmake
          ninja
          gcc
          pre-commit
        ]);
      shellHook = ''
        # Unset leaky PYTHONPATH
        unset PYTHONPATH

        __py_hash=$(echo ${python.interpreter} | sha256sum)
        __node_hash=$(echo ${pkgs.lib.getExe node} | sha256sum)

        # Setup venv
        if [[ ! -f ".venv/$__py_hash" ]]; then
            __setup_env() {
                # Remove existing venv
                if [[ -d .venv ]]; then
                    rm -r .venv
                fi

                # Stand up new venv
                ${python.interpreter} -m venv .venv

                ".venv/bin/python" -m pip install jupyterlab -e .

                # Add a marker that marks this venv as "ready"
                touch ".venv/$__py_hash"
            }

            __setup_env
        fi

        # Setup node modules
        if [[ ! -f "node_modules/$__node_hash" ]]; then
            # Remove existing modules
            if [[ -d node_modules ]]; then
                rm -r node_modules
            fi
            '${pkgs.lib.getExe' node "npm"}' install
            touch "node_modules/$__node_hash"
        fi
        ###########################
        # Activate venv
        source .venv/bin/activate
      '';
      env = lib.optionalAttrs pkgs.stdenv.isLinux {
        # Python uses dynamic loading for certain libraries.
        # We'll set the linker path instead of patching RPATH
        LD_LIBRARY_PATH = lib.makeLibraryPath pkgs.pythonManylinuxPackages.manylinux2014;
      };
    in {
      devShell = pkgs.mkShell {
        inherit env packages shellHook;
      };
    });
}
