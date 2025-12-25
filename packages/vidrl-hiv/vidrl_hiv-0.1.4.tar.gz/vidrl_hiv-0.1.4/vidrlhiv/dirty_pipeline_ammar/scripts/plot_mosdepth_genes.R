pacman::p_load(ggplot2, dplyr, optparse, tidyr,  cowplot)

option_list <- list(
    make_option(c("-i","--input"), help = "input tsv from samtools depth", 
                action="store", type="character", default=NA),
    make_option(c("-o","--output"),help = "output name without extension", 
                action="store", type="character", default=NA),
    make_option(c("-s","--sample_name"),help = "sample name", 
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
    error = function(e) { print(e)}
)

if (any(is.na(arguments$options))) {
    stop_quietly(parser$usage)
}

if (interactive()) {
    arguments = list(
        input = "../output/all.gene.bed",
        output = "../output/genes.pdf"
    )
}

depth = read.csv(arguments$input, sep = "\t")
depth = depth %>%
    #separate(col = sample, into = c( "runid", "sampleid"), sep = "_", remove = FALSE) %>%
    mutate(grade = case_when(depth < 50 ~ "bad(depth < 50)",
                             depth > 50  & depth < 100 ~ "fine ( > 50 & < 100)",
                             depth > 100 & depth < 500 ~ "good (> 100 & < 500)",
                             depth > 500 & depth < 1000 ~ "excellent (> 500 & < 1000)",
                             depth > 1000 ~ "abundant (>1000)",
                             TRUE ~ NA_character_))
                            
depth$grade <- factor(depth$grade,
                  levels = c("bad(depth < 50)", "fine ( > 50 & < 100)", 
                  "good (> 100 & < 500)", "excellent (> 500 & < 1000)",
                  "abundant (>1000)"))
combine_id <- function(x){
    if (grepl("_", x)){
        y <- sub("^([^_]*)_(.*)$", "\\2_\\1", x)
    return(y)
    } else {
        return(x)
    }
}

color_vector = c(
    "bad(depth < 50)" = "grey",
    "fine ( > 50 & < 100)" = "brown",
    "good (> 100 & < 500)" = "blue",
    "excellent (> 500 & < 1000)" = "green",
    "abundant (>1000)" = "coral"
)

##re-write the plot section
plot_list <- list()
count <- 1
label_vector <- c()
sample_list <- unique(depth$sample)
sort_idx <- order(combine_id(sample_list))
sorted_sample_list <- sample_list[sort_idx]
for (s in sorted_sample_list){
    sub_df <- depth %>% filter(sample == s)
    p <- ggplot(sub_df, aes(x=gene, y=depth)) +
        geom_col(aes(fill=grade)) +
        ggtitle(s) +
        scale_y_continuous(trans='log10') +
        #facet_grid(runid~sampleid) + 
        #facet_grid(sample~.) +
        theme_classic() +
        scale_fill_manual(values=color_vector) +
        theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1),
        plot.title = element_text(size = 15, face = "bold"))
    plot_list[[count]] <- p
    label_vector <- c(label_vector, s)
    count <- count + 1
}

#save the joint plots
highC <- length(unique(depth$sample))


##old way to calculate nol
# ncol <- highC %/% 6
# if (ncol %% 6 != 0){
#     ncol <- ncol + 1
# }
# nrow <- 1
# if (highC > 6){
#     nrow <- 6
# } else {
#     nrow <- highC
# }

ncol <- ceiling(sqrt(highC))
nrow <- ncol

combined_plots <- plot_grid(plotlist=plot_list, ncol=ncol)
#ggexport(combined_plots, filename=arguments$output, width=210*ncol, height=210*nrow, unit="mm") 
wid = min(200*ncol, 1260)
hei = min(210*nrow, 1260)
ggsave(arguments$output, combined_plots, width = wid, height = hei, unit = "mm")

# highC <- length(unique(depth$sample))
# plot = ggplot(depth, aes(x = gene, y = depth)) + 
#     geom_col(aes(fill=grade)) +
#     scale_y_continuous(trans='log10') +
#     #facet_grid(runid~sampleid) + 
#     facet_grid(sample~.) +
#     theme_classic() +
#     theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))

# #calculate number of samples in the run to make the plot readable
# #highC <- length(unique(depth$sample))
# #save the plot
# #ggsave(arguments$output, plot, width = 297*2, height = 210*highC, unit = "mm")
# ggsave(arguments$output, plot, width = 210, height = 210*highC, unit = "mm")
