# Render the latency report to docs/ for GitHub Pages hosting
# Run this script from the repository root directory
#
# Usage:
#   Rscript render.R
#   - or in RStudio: source("render.R")

# Install required packages if needed
required_packages <- c("tidyverse", "ggplot2", "gsheet", "DT", "crosstalk", "plotly", "htmlwidgets", "rmarkdown")

for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message(paste("Installing", pkg, "..."))
    install.packages(pkg, repos = "https://cran.rstudio.com/")
  }
}

# Render the report
message("Rendering input.Rmd to docs/input.html...")

rmarkdown::render(
  input = "rpubs/input.Rmd",
  output_file = "input.html",
  output_dir = "docs/",
  quiet = FALSE
)

message("Done! Output saved to docs/input.html")
message("GitHub Pages URL: https://misteraddons.github.io/inputlatency/")
