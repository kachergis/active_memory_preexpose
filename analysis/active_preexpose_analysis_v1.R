require(ggplot2)
require(dplyr)

setwd("/Users/george/active_memory_preexpose/analysis")

analyze_summary_data <- function() {
  d = read.csv("results.csv", header=T)
  dim(d)
  table(d$nStudiedActive)
  hist(d$FA)
  hist(d$CR)
  hist(d$nStudiedActive)
  plot(d$CR, d$FA)
  plot(d$nStudiedActive, d$CR)
  cor.test(d$nStudiedActive, d$CR) # .19 p=.07
}

preexpose_inds = list('left'=c(0,1,4,5), 'right'=c(2,3,6,7), 'all'=c(0,1,2,3,4,5,6,7))
# preexpose_inds[['left']]

preprocess <- function() {
  sdat = read.csv("study_trials.csv", header=T)
  tdat = read.csv("test_trials.csv", header=T)
  sloc = read.csv("study_locations.csv", header=T)
  # for reasons unknown, it looks like some of the studied items (in sloc and sdat)
  # were not tested...despite there being 24 'old' items tested per subject (!)
  # need to figure this out: match sloc$item to tdat$item...
  
  tdat$correct = ifelse(tdat$correct=='True', 1, 0)
  print(paste(length(unique(sdat$subj)), "subjects")) # 84 in sdat, 80 in tdat
  incomplete_subjs = which(table(tdat$subj)!=48) # or duplicate? 11318, 11215, and 1065 have >48
  tdat = subset(tdat, !is.element(subj, names(incomplete_subjs))) # 3456 of 3732 remain
  sdat = subset(sdat, !is.element(subj, names(incomplete_subjs))) # 1909 of 2051 remain
  # 43 of the first study episodes have negative durations; could make them NA, but it looks like stopt has the right time (range: 55-6770)
  sdat[which(sdat$duration<0),]$duration = sdat[which(sdat$duration<0),]$stopt 
  maxDur = median(sdat$duration) + 2*sd(sdat$duration) # 1427 + 2*1783 = 4993
  sdat = subset(sdat, duration<maxDur) # eliminates 94 of 1909
  sdat = subset(sdat, duration>100) # eliminates 19
  print(paste(length(unique(tdat$subj)), "subjects")) # now 76 in sdat and 72 in tdat...
  sdat = subset(sdat, is.element(subj, unique(tdat$subj))) # okay, 72 subjects
  print(summary(sdat$duration))
  dim(subset(sdat))
  tdat$studycond = NA
  tdat$preexposed = NA
  tdat$study_reps = NA
  tdat$study_time = NA
  tdat$study_loc = NA
  tdat$study_block = NA
  tdat$in_sloc = F # was actually in sloc (all old things should be)
  #tdat$mean_study_time = NA
  missing_stud_items = 0
  for(r in 1:nrow(tdat)) {
    s = tdat[r,]$subj
    it = tdat[r,]$item
    # find corresponding study episodes and count number and total study duration
    # also tag preexposed vs. not items
    tmp = subset(sdat, subj==s & it==id)
    
    locind = which(sloc$subj==s & sloc$item==it)
    if(length(locind)>0) {
      sloc_r = sloc[locind,]
      tdat[r,]$in_sloc = T
      tdat[r,]$study_block = sloc_r$block
      tdat[r,]$study_loc = sloc_r$loc
    }
    
    if(nrow(tmp)!=0) {
      tdat[r,]$studycond = tmp$preexpose[1]
      tdat[r,]$study_time = sum(tmp$duration)
      tdat[r,]$preexposed = ifelse(tmp[1,]$preexpose=="all" | 
                                   tmp[1,]$preexpose=="left" & is.element(tmp[1,]$item, preexpose_inds[["left"]]) |
                                   tmp[1,]$preexpose=="right" & is.element(tmp[1,]$item, preexpose_inds[["right"]]), 1, 0)
      tdat[r,]$study_reps = nrow(tmp)
    } 
    # if they never studied an item, to match the info at test we'll need to go back to the preexpose period data...(annoying)
    #if(nrow(tmp)!=1) print(paste("item mismatch:",s, it))
  }
  
  return(list(dat=tdat, sdat=sdat, sloc=sloc))
}

all = preprocess()

snum = aggregate(correct ~ subj + cond + in_sloc, length, data=all$dat) 

surplus_old = subset(all$dat, cond=="active" & in_sloc==F) # 455...~6 per subject (25% of the data :/)

old = subset(all$dat, in_sloc==T)
oag = aggregate(c(correct, study_time, study_reps) ~ subj, mean, data=old) 


all$dat %>%
  group_by(subj, cond) %>%
  select(correct, study_reps, study_time) %>%
  summarise(
    correct = mean(correct, na.rm = TRUE),
    time = mean(study_time, na.rm = TRUE),
    reps = mean(study_reps, na.rm = TRUE)
  ) # %>% filter(arr > 30 | dep > 30)

sag = aggregate(correct ~ subj + cond, mean, data=all$dat) 
aggregate(correct ~ cond, mean, data=tdat) 