push <- function(msg = paste("Mise à jour", Sys.Date())) {
  system("git add -A")
  system(sprintf('git commit -m "%s"', msg))
  system("git push")
}
