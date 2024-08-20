# quarto-agent
A GenAI Agent that iterates creation and rendering of Quarto artifacts

## Install

Install Quarto: https://quarto.org/docs/get-started/

Install Sunholo CLI https://dev.sunholo.com/docs#getting-started

Create a `.venv`

Run project init:

```bash
sunholo init quarto
cd quarto
```

Passing around markdown in HTTP is a reall bad idea as it gets into escape chaarcter hell, pass the files instead.

## Examples using curl

```bash
export FLASK_URL=http://127.0.0.1:8080

curl -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Report if quarto is working"
}'
```

```bash
----Loop [0]------
# quarto_version({}) result:
OK: 

[✓] Checking versions of quarto binary dependencies...
      Pandoc version 3.1.1: OK
      Dart Sass version 1.55.0: OK

[✓] Checking versions of quarto dependencies......OK

[✓] Checking Quarto installation......OK
      Version: 1.3.450
      Path: /Applications/quarto/bin


(|) Checking basic markdown render....
(/) Checking basic markdown render....
(-) Checking basic markdown render....
(\) Checking basic markdown render....

[✓] Checking basic markdown render....OK


(|) Checking Python 3 installation....
(/) Checking Python 3 installation....

[✓] Checking Python 3 installation....OK
      Version: 3.12.3
      Path: /Users/mark/dev/sunholo/quarto-agent/.venv/bin/python3
      Jupyter: 5.7.2
      Kernels: python3


(|) Checking Jupyter engine render....
(/) Checking Jupyter engine render....
(-) Checking Jupyter engine render....
(\) Checking Jupyter engine render....
(|) Checking Jupyter engine render....
(/) Checking Jupyter engine render....
(-) Checking Jupyter engine render....
(\) Checking Jupyter engine render....
(|) Checking Jupyter engine render....
(/) Checking Jupyter engine render....
(-) Checking Jupyter engine render....
(\) Checking Jupyter engine render....
(|) Checking Jupyter engine render....
(/) Checking Jupyter engine render....
(-) Checking Jupyter engine render....
(\) Checking Jupyter engine render....
(|) Checking Jupyter engine render....
(/) Checking Jupyter engine render....
(-) Checking Jupyter engine render....
(\) Checking Jupyter engine render....

[✓] Checking Jupyter engine render....OK


(|) Checking R installation...........
(/) Checking R installation...........

[✓] Checking R installation...........OK
      Version: 4.2.1
      Path: /Library/Frameworks/R.framework/Resources
      LibPaths:
        - /Users/mark/Library/R/x86_64/4.2/library
        - /Library/Frameworks/R.framework/Versions/4.2/Resources/library
      knitr: 1.40
      rmarkdown: 2.17


(|) Checking Knitr engine render......
(/) Checking Knitr engine render......
(-) Checking Knitr engine render......
(\) Checking Knitr engine render......
(|) Checking Knitr engine render......
(/) Checking Knitr engine render......
(-) Checking Knitr engine render......

[✓] Checking Knitr engine render......OK


----Loop [0] End------

----Loop [1]------


STOPPING: Quarto is installed and working
```

Do the demo.qmd:

```bash
curl -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Please render the demo Quarto page"
}'
----Loop [0]------
# render_and_upload_quarto({}) result:
{"status": "success", "gcs_url": "gs://multivac-internal-dev-dev-vertex-extensions/output.html", "stdout": "", "stderr": "\nStarting python3 kernel...Done\n\nExecuting 'demo.ipynb'\n  Cell 1/1...Done\n\n\u001b[1mpandoc --output ../output.html\u001b[22m\n  to: html\n  standalone: true\n  section-divs: true\n  html-math-method: mathjax\n  wrap: none\n  default-image-extension: png\n  \n\u001b[1mmetadata\u001b[22m\n  document-css: false\n  link-citations: true\n  date-format: long\n  lang: en\n  title: Quarto Agent Basics\n  \nOutput created: ../output.html\n\n"}
----Loop [0] End------

----Loop [1]------


STOPPING: The user asked to render the demo Quarto page and the agent successfully rendered the page.
----Loop [1] End------
```

Execute your own QMD files:

```bash
curl -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: multipart/form-data" \
  -F "user_input=Please render this markdown file" \
  -F "file=@tools/demo.qmd"
----Loop [0]------
# render_and_upload_quarto({"markdown_filename": "/Users/mark/dev/sunholo/quarto-agent/quarto/renders/tmpfqf558x8.qmd"}) result:
{"status": "success", "gcs_url": "gs://multivac-internal-dev-dev-vertex-extensions/output.html", "stdout": "", "stderr": "\nStarting python3 kernel...Done\n\nExecuting 'tmpfqf558x8.ipynb'\n  Cell 1/1...Done\n\n\u001b[1mpandoc --output ../output.html\u001b[22m\n  to: html\n  standalone: true\n  section-divs: true\n  html-math-method: mathjax\n  wrap: none\n  default-image-extension: png\n  \n\u001b[1mmetadata\u001b[22m\n  document-css: false\n  link-citations: true\n  date-format: long\n  lang: en\n  title: Quarto Agent Basics\n  \nOutput created: ../output.html\n\n"}
----Loop [0] End------

----Loop [1]------


STOPPING: The user asked to render a markdown file and the file was rendered successfully.
----Loop [1] End------
```