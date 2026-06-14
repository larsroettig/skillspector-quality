# Homebrew formula for skillspector-quality.
#
# This file lives in Formula/ inside the project repo. To publish it:
#
#   1. Create a GitHub repo named  homebrew-tap  (or any name)
#   2. Copy this file into that repo at  Formula/skillspector-quality.rb
#   3. Users install with:
#        brew tap lroettig/tap https://github.com/lroettig/homebrew-tap
#        brew install skillspector-quality
#
# Before publishing:
#   • Replace every PLACEHOLDER_* value (URL + sha256).
#   • Run `brew audit --new Formula/skillspector-quality.rb` to validate.
#   • Run `brew test skillspector-quality` to verify the test block.
#
# Generating sha256 for a tarball:
#   curl -sL <url> | sha256sum
#
# Generating the resource stanzas for all Python deps automatically:
#   pip install homebrew-pypi-poet
#   poet --formula skillspector-quality   (run after `pip install skillspector-quality`)

class SkillspectorQuality < Formula
  include Language::Python::Virtualenv

  desc "Deterministic authoring quality scorer for Claude Code skills (0-100)"
  homepage "https://github.com/lroettig/skillspector-quality"

  # Replace with the URL of your GitHub release tarball and its sha256.
  url "https://github.com/lroettig/skillspector-quality/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER_SKILLSPECTOR_QUALITY_SHA256"

  license "MIT"

  depends_on "python@3.13"

  # --------------------------------------------------------------------------
  # skillspector — upstream security scanner, not on PyPI.
  # Replace URL + sha256 with your SkillRater release tarball.
  # --------------------------------------------------------------------------
  resource "skillspector" do
    url "https://github.com/PLACEHOLDER_OWNER/SkillRater/archive/refs/tags/v2.1.4.tar.gz"
    sha256 "PLACEHOLDER_SKILLSPECTOR_UPSTREAM_SHA256"
  end

  # --------------------------------------------------------------------------
  # Python runtime dependencies.
  # Run `poet --formula skillspector-quality` to regenerate these stanzas
  # with exact versions and checksums after each release.
  # --------------------------------------------------------------------------
  resource "typer" do
    url "https://files.pythonhosted.org/packages/PLACEHOLDER_TYPER.tar.gz"
    sha256 "PLACEHOLDER_TYPER_SHA256"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/PLACEHOLDER_RICH.tar.gz"
    sha256 "PLACEHOLDER_RICH_SHA256"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/PLACEHOLDER_PYYAML.tar.gz"
    sha256 "PLACEHOLDER_PYYAML_SHA256"
  end

  # Add all transitive deps reported by `poet` here.

  def install
    # Create an isolated virtualenv so the tool doesn't pollute Homebrew's Python.
    venv = virtualenv_create(libexec, "python3.13")

    # Install skillspector first — it is not on PyPI so we install from source.
    resource("skillspector").stage do
      venv.pip_install_and_link buildpath
    end

    # Install all remaining resources (pip dependencies).
    venv.pip_install resources.reject { |r| r.name == "skillspector" }

    # Install skillspector-quality itself.
    venv.pip_install_and_link buildpath

    # Expose the binary.
    bin.install_symlink libexec/"bin/skillspector-quality"
  end

  test do
    # Smoke-test: --help must exit 0 and print the command name.
    assert_match "skillspector-quality", shell_output("#{bin}/skillspector-quality --help")

    # Functional test: scan a minimal skill and expect a non-error exit.
    (testpath/"SKILL.md").write <<~MARKDOWN
      ---
      name: brew-test
      description: Minimal skill for Homebrew formula test.
      ---
      # Brew test skill

      This skill exists to verify the Homebrew formula installs and runs correctly.
    MARKDOWN
    system bin/"skillspector-quality", "scan", testpath.to_s, "--no-llm"
  end
end
