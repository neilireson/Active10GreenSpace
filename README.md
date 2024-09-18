# Active10GreenSpace
Code to process the Active10 dataset to correlate steps with Greenspace proximity and area

By default min_step_threshold = 500, meaning that days with fewer than 500 steps are ignored

For (all and active) walking, all days with walking steps greater than 0 are included. This is because the person is deemed to be carrying their phone, as they have >= 500 steps, but may not go for any (active) walks.
Note that it is arguable that days with zero walking days should be included.

