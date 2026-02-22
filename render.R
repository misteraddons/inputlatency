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
if (dir.exists("docs/input_libs")) {
  unlink("docs/input_libs", recursive = TRUE)
}
if (dir.exists("rpubs/input_libs")) {
  unlink("rpubs/input_libs", recursive = TRUE)
}

rmarkdown::render(
  input = "rpubs/input.Rmd",
  output_file = "input.html",
  output_dir = "docs/",
  output_options = list(
    self_contained = FALSE,
    lib_dir = "../docs/input_libs"
  ),
  clean = TRUE,
  quiet = FALSE
)

output_file <- "docs/input.html"
if (file.exists(output_file)) {
  output_size_mb <- file.info(output_file)$size / (1024 * 1024)
  message(sprintf("Output size: %.2f MB", output_size_mb))
}

message("Done! Output saved to docs/input.html")
message("GitHub Pages URL: https://misteraddons.github.io/inputlatency/")
