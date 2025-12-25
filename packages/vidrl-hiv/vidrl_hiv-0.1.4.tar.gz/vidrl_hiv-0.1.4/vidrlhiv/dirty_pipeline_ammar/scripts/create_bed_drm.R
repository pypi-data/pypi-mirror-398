pacman::p_load(dplyr, tidyr)

gag = list("start" = 790, end = 2292)
PR = list("start" = 2253, end = 2550)
RT = list("start" = 2550, end = 3870)
integrase = list("start" = 4230, end = 5096)
env = list("start" = 6225, end = 8795)

create_bed = function(path) {
  df = read.csv(path, sep = "\t") %>%
    distinct(Gene, Position, .keep_all = TRUE) %>%
    mutate(Gene = case_when(Gene == "IN" ~ "integrase", TRUE ~ Gene)) %>%
    mutate(nt_pos = case_when(
      Gene == "PR" ~ (Position*3) + PR$start,
      Gene == "RT" ~ (Position*3) + RT$start,
      Gene == "integrase" ~ (Position*3) + integrase$start,
      TRUE ~ 0
    )
  ) %>%
    mutate(start = nt_pos - 5, end = nt_pos + 5)

  bed = data.frame(
    chrom = "K03455.1",
    start = df$start,
    end = df$end,
    gene = df$Gene
  )
  return(bed)
}

bed = create_bed(path = "resources/drm.tsv")
write.table(
  bed, "resources/drm.bed", sep = "\t", row.names = F, quote = F,
  col.names = c("#chrom", "start", "end", "gene")
)
