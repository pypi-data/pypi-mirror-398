pacman::p_load(ggplot2, dplyr, optparse)

option_list <- list(
    make_option(c("-i","--input"), help = "input tsv from samtools depth", 
                action="store", type="character", default=NA),
    make_option(c("-o","--output"),help = "output name without extension", 
                action="store", type="character", default=NA)
)
parser <- OptionParser(
    usage = paste("%prog -i [INPUTDIR] -o [OUTPUTDIR]",
                  "Script to plot genotype specific trees", sep="\n"),
    epilogue = "INPUT, OUTPUT are required",
    option_list=option_list)

#custom function to stop quietly
stop_quietly = function(message) {
    opt = options(show.error.messages = FALSE)
    on.exit(options(opt))
    cat(message, sep = "\n")
    quit()
}

arguments=NA
tryCatch(
    { arguments = parse_args(object = parser, positional_arguments = FALSE) },
    error = function(e) { }
)

if (any(is.na(arguments$options))) {
    stop_quietly(parser$usage)
}

if (interactive()) {
    arguments = list(
        input = "output/all.genome.bed",
        output = "~/Desktop/tmp.pdf"
    )
}

depth = read.csv(arguments$input, sep = "\t")

depth = depth %>%
    mutate(cutoffs = case_when(
        depth == 0 ~ "zero",
        depth < 100 ~ "below100",
        depth < 1000 ~ "below1k",
        TRUE ~ "above1k"),
    depth2 = case_when(depth == 0 ~ 1, TRUE ~ depth)
    )

plotheat = ggplot(depth, aes(
        x = pos,
        y = sample, 
        fill = depth2)) + 
    geom_tile() + scale_fill_viridis_c()

ggsave(arguments$output, plotheat, width = 297, height = 210, units = "mm")
