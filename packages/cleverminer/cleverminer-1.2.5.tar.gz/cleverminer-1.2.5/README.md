# CleverMiner

<img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/cleverminer">
<img alt="PyPI - Wheel" src="https://img.shields.io/pypi/wheel/cleverminer">
<img alt="PyPI - Status" src="https://img.shields.io/pypi/status/cleverminer">
<img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/cleverminer">

## The CleverMiner is an enhanced association rule mining library 

Beyond apriori. CleverMiner is the package for enhanced association rule mining (eARM), that are INTERPRETABLE, so by definition   one of few intrinsic methods of explainable AI (XAI). Comparing to standard association rules, it is very enhanced, because the package implements the GUHA procedures that generalizes apriori and association rules in many ways. Rules are based on categorical data that can be easily visualized and interpreted. Their if-then with probability allows easy deployment by human realized processes. Interpretable & explainable knowledge mining.

## The CleverMiner in more detail

In general, apriori is looking for rules {ItemSet} -> {Item} (Base, prob). GUHA goes further and instead of items (boolean attributes), list of categorial attributes and combination of values (nominal and several strategies for ordinal -- joining categories) is searched on left and right hand side. Moreover, GUHA has much more possibilites and several other procedures, like mining interesting histograms, finding couples of rules etc.

To run cleverminer procedures, use dataframe with categorical variables only. Cleverminer prepares all variables and values for future reuse.

## Optimized in many ways

CleverMiner has optimized space search in several ways. 

- first, it encodes dataframe into internal format that is optimized for frequent querying for similar pattern, then it queries the dataframe many (typically several thousand or tens/hunderds thousand) times. 
- the algorithm has also optimizations by the derived properties of individual procedures (e.g. when procedure A finds that expanding rule will in every case lead into rules that does not meet requirements, it skips entire branch). This optimization typically reduces the mining time significantly.


## CleverMiner documentation

Documentation for CleverMiner can be found at [cleverminer.org](https://cleverminer.org)

## What's new

1.2.5
- Double implication and equivalence quantifiers for 4ft-Miner
- Unit tests

1.2.4
- GNU GPLv3

1.2.3
- added actplusminer

1.2.2
 - minor fixes for non-standard applications

1.2.1
 - load can be invoked in constructor (cleverminer(load="filename.ext"))
 - load support urls
 - clm_vars - task can be defined more easily
 - cache save more reliable

1.2.0
 - load and save methods available to save your results for future use
 - cache results - results are cached and if task is found in cache, it is not recalculated again (use "use_cache":True option)

1.1.1 
 - rich API available
 - new detailed documentation available at [cleverminer.org](https://cleverminer.org)
 - minor bugfixes


1.1.0 (cumulative feature update)
 - support for displaying charts for rules (.draw_rule() method)
 - procedures fully documented (docstrings available)
 - UIC Miner supports relevant base lift and relevant cat base quantifiers
 - support for lambda quantifiers
 - support for list literal type
 - improved detection of ordered categories


1.0.12
 - fixed problem with .mine method ("row_count" issue)

1.0.11
 - fixed wording in UIC miner output
 - fixed bug in dataset description

1.0.10
 - get_ruletext method
 - result contains rowcont of original dataframe to increase possibilities of post-processing

1.0.9
 - fixed bugs - error message when displaying of results that has not been calculated
 - Python 3.12 regression tests passed ok

1.0.8
 - data preparation enhanced in many ways
 - able to work with series like 1,2,3, 4-20, 21 and more, 0.0,1.0, ..., Temp 17-25oC,...


1.0.7
 - CF miner supports step size and range between relmax & relmin
 - categories printed in CF output
 - bugfix: checking number of categories fixed
 - can return also adjusted df (ordered categories, ...) - functionality not guaranteed to future

1.0.6
 - progressbar

1.0.5

 - supports missing pandas functionalities and implements several automated data preprocessing
 - listing of variables, ordering and labels
 - automatically process conversion to numeric, integers and order float & integer variables
 - fixed verbosity level prints

1.0.4
 - sorting output rules

1.0.3
 - UIC Miner introduced

1.0.2
 - merge changes from 0.91 (data structure checks; as 1.0.0 was build from 0.0.90 so remaining features are merged now)

1.0.1
 - new procedures get4fold, gethist, getquantifiers, getrulecount

1.0.0 - Major release, major rebuild from all views:
 - data import reworked and fastened significantly
 - much faster calculation (rule mining) in Py3.10 + next optimizations for rule mining are in place
 - output structure is enhanced, fully structured output is available for post-processing (trace_cedent, cedent_struct in output)
 - data can be read once and multiple tasks can be performed (.mine method)
 - optimizations for sd4ft miner
 - verbosity options available (run progress output has been changed)
 - additional options available (able to override maximum number of categories)
 - better formatting outputs (bugfix)
 - data structure in output has changed

0.0.91 - detect error in datatypes in input data and correctly report it

0.0.90 - fix in displaying rules for 4ft-Miner, in CF-Miner: allowing relmax to be bounded from both sides (leq introduced), in SD4ft-Miner: allowing ratioconf to be bounded from both sides (leq introduced)

0.0.89 - quantifiers and output dictionary names change in favor of rules terminology (output: hypotheses->rules; hypo_id -> rule_id, quantifiers kept 
for compatibility old and new names, including variability (like frstbase -> also base1 is possible)

0.0.88 - print of task summary, hypo listing and individual hypothesis

0.0.87 - support for 'one category' added

0.0.86 - bugfixes (space search for optimized branch, able to switch off optimization, minimal cedent length bug for optimized search)

0.0.85 - bugfixes (row_count), checking input structure

0.0.84 - optimizations for conjunctions

 


