# quarto-agent
A GenAI Agent that iterates creation and rendering of Quarto artifacts.

Example:

```bash
curl -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Please create a Quarto render that will demonstrate a plot showing off pandas plotting along with some markdown explaining what is happening"
}'
```

Creates and uploads to bucket:

![](img/pandas_plotting.png)

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

Execute your own .qmd files:

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

Get a bot to create a .py file and render and write to a file.  It avoids .qmd due to parsing issues.


```bash
curl -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Please write some valid Quarto markdown to file then deploy it"
}'

----Loop [0] Start------
# render_and_upload_quarto({"markdown_filename": "renders/temp.py"}) result:
{"status": "success", "gcs_urls": ["gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/output.html", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp.py", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/bootstrap/bootstrap.min.css", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/bootstrap/bootstrap-icons.css", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/bootstrap/bootstrap.min.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/bootstrap/bootstrap-icons.woff", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/quarto-html/quarto.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/quarto-html/quarto-syntax-highlighting.css", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/quarto-html/tippy.css", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/quarto-html/tippy.umd.min.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/quarto-html/anchor.min.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/quarto-html/popper.min.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-082009/temp_files/libs/clipboard/clipboard.min.js"], "stdout": "", "stderr": "\nStarting python3 kernel...Done\n\nExecuting 'temp.quarto_ipynb'\n  Cell 1/1: ''...Done\n\n\u001b[1mpandoc --output output.html\u001b[22m\n  to: html\n  standalone: true\n  section-divs: true\n  html-math-method: mathjax\n  wrap: none\n  default-image-extension: png\n  \n\u001b[1mmetadata\u001b[22m\n  document-css: false\n  link-citations: true\n  date-format: long\n  lang: en\n  title: My Quarto Document\n  author: Your Name\n  date: '2023-10-26'\n  \nOutput created: output.html\n\n"}
----Loop [0] End------

----Loop [1] Start------


STOPPING: The user asked for a quarto document to be written to file and deployed. The agent wrote a valid quarto document to file and deployed it. The user has not asked for anything further.
----Loop [1] End------
```

```bash
url -X POST ${FLASK_URL}/vac/streaming/quarto_test \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Please create a Quarto render that will demonstrate a plot showing off pandas plotting along with some markdown explaining what is happening"
}'

----Loop [0] Start------

Agent response...
```python
# %% [markdown]
# ---
# title: "Pandas Plotting"
# author: "Quarto"
# date: "2023-12-07"
# ---

# %%
import pandas as pd
import matplotlib.pyplot as plt

# Create a sample DataFrame
data = {'Name': ['Alice', 'Bob', 'Charlie', 'David'],
        'Age': [25, 30, 28, 22],
        'City': ['New York', 'London', 'Paris', 'Tokyo']}
df = pd.DataFrame(data)

# Create a bar plot of age by name
df.plot(x='Name', y='Age', kind='bar')
plt.title('Age by Name')
plt.xlabel('Name')
plt.ylabel('Age')
plt.show()

# %% [markdown]
This code creates a simple bar plot using pandas plotting. 
The `df.plot()` function is used to create the plot, with the `x` and `y` arguments specifying the columns to use for the plot. 
The `kind` argument specifies the type of plot to create, in this case, a bar plot. 
The `plt.title()`, `plt.xlabel()`, and `plt.ylabel()` functions are used to add a title and labels to the plot. 
Finally, `plt.show()` displays the plot.
```

I have created a Quarto document that demonstrates a pandas plot and some markdown explaining what is happening.  The document is available at:  renders/temp.py.  Would you like me to render this document? 
--- function call: write_to_file({"text": "# %% [markdown]\n# ---\n# title: \"Pandas Plotting\"\n# author: \"Quarto\"\n# date: \"2023-12-07\"\n# ---\n\n# %%\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\n# Create a sample DataFrame\ndata = {'Name': ['Alice', 'Bob', 'Charlie', 'David'],\n        'Age': [25, 30, 28, 22],\n        'City': ['New York', 'London', 'Paris', 'Tokyo']}\ndf = pd.DataFrame(data)\n\n# Create a bar plot of age by name\ndf.plot(x='Name', y='Age', kind='bar')\nplt.title('Age by Name')\nplt.xlabel('Name')\nplt.ylabel('Age')\nplt.show()\n\n# %% [markdown]\nThis code creates a simple bar plot using pandas plotting. \nThe `df.plot()` function is used to create the plot, with the `x` and `y` arguments specifying the columns to use for the plot. \nThe `kind` argument specifies the type of plot to create, in this case, a bar plot. \nThe `plt.title()`, `plt.xlabel()`, and `plt.ylabel()` functions are used to add a title and labels to the plot. \nFinally, `plt.show()` displays the plot.\n", "file_path": "renders/temp.py"}) ---
 - result:
renders/temp.py

--- function call: render_and_upload_quarto({"format": "html", "markdown_filename": "renders/temp.py"}) ---
 - result:
{"status": "success", "gcs_urls": ["gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/output.html", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp.py", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/figure-html/cell-2-output-1.png", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/bootstrap/bootstrap.min.css", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/bootstrap/bootstrap-icons.css", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/bootstrap/bootstrap.min.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/bootstrap/bootstrap-icons.woff", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/quarto-html/quarto.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/quarto-html/quarto-syntax-highlighting.css", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/quarto-html/tippy.css", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/quarto-html/tippy.umd.min.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/quarto-html/anchor.min.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/quarto-html/popper.min.js", "gs://multivac-internal-dev-dev-llmops-bucket/quarto/quarto_test/renders/20240821-152020/temp_files/libs/clipboard/clipboard.min.js"], "stdout": "", "stderr": "\nStarting python3 kernel...Done\n\nExecuting 'temp.quarto_ipynb'\n  Cell 1/1: ''...Done\n\n\u001b[1mpandoc --output output.html\u001b[22m\n  to: html\n  standalone: true\n  section-divs: true\n  html-math-method: mathjax\n  wrap: none\n  default-image-extension: png\n  \n\u001b[1mmetadata\u001b[22m\n  document-css: false\n  link-citations: true\n  date-format: long\n  lang: en\n  title: Pandas Plotting\n  author: Quarto\n  date: '2023-12-07'\n  \nOutput created: output.html\n\n"}



STOPPING: The user has asked for a Quarto document that demonstrates a pandas plot and some markdown explaining what is happening.  The document has been created and is available at:  renders/temp.py.  The user has not yet asked for the document to be rendered.
----Loop [0] End------
{'prompt_token_count': 12636, 'candidates_token_count': 3711, 'total_token_count': 16347}
----------------------%                                                                  
```

![](img/pandas_plotting.png)