# Colonial Korea Periodicals Archive



This is a [site](https://yeoksayeou.github.io/) created mostly for students of history to easily browse articles of several Korean colonial period journals. 

The articles displayed here are transcriptions of Korean colonial period magazines that are *already available online*. This site only possible thanks to the transcription work of the [National Institute of Korean History](https://db.history.go.kr/) (국사편찬위원회). Their incredible work has provided an immensely important contribution to the study of Korean history. This site has no connection to the institute but has assembled and reproduced its transcriptions for these journals here. The original journals are assumed to be in the public domain and the pages for them are linked from each magazine page and issue tables of contents.

The institute's [Database of Korean History: Modern Korea](https://db.history.go.kr/modern/) contains a huge array of important historical materials related modern Korean history, including transcriptions of articles for a number of journals such as those reassembled here. This website does not fully reproduce the rich functionality of the original database, which often includes links to images of the original files and allows convenience saerch across all of its holdings. 

So why create this site if they are already online? This site makes it easy to conveniently download a *full* local collection of these specific files for those who want to explore them quickly on their own computer for purposes of study and research. To do this, download the entire [repository](https://github.com/yeoksayeou/yeoksayeou.github.io) for this website and open the webpage locally on your own machine. Open the "index.html" file and you should see this same content and things will run much faster. Also note that each journal has, in its footer, a link to the specific journal home page on the 국사편찬위원회. Warm thanks to them for making their materials open and accessible to researchers everywhere.

**Notes on the Translations**

The other and perhaps most important added feature of this project is an experimental one: translations. Large language model English-translated versions of the articles have been added to make these journals more accessible for students who do not know Korean, who are learning Korean but may still be early on their journey to learning hanja, or who may know Korean but find reading these Sino-Korean and Japanese language texts troublesome enough that it is helpful to have a rough English translation to refer to while scanning over the issues. 

*Does the usefulness of these translations outweigh problems they pose? How bad or good are they? What do they struggle with and what do they do well? These are questions I hope that students and researchers will consider as they explore the translations included here.*

For some of the translations here, the LLM was asked to extract a list of named entities, a glossary of vocabulary, and a short summary. The LLM used was Gemini 2.5 for three of the journals, and Gemini 2.0 for *Pyŏlgŏn'gon*, which produced poorer quality translations.

The LLM translation exhibit all the usual problems of large language models. Be on the look out for hallucinations as well as a host of mistakes based on its incorrect translation of words from the Korean colonial context. These translations should not be quoted without first checking their accuracy and correcting them accordingly.

*Example One*: One file that had metadata, including title, but no content, in the original Korean version, produced a "translation" that completely hallucinated an entire article from the title alone. While that case was spotted, there are no doubt other examples of this kind of behavior in the LLM translations here. 

*Example Two*: If there is a mistranslation of a word, based on a misunderstanding of the context, this may heavily impact the translation of the remainder of the article. If words are assumed to be a Korean spelling of a Western name, for example, but in fact it is some other word entirely, that can change the contents significantly for the remainder of the translation. 

*Example Three:* The glossaries, when they are provided, may not provide the definition most appropriate for the article if the LLM, even if it was correctly translated in the original text.

*Example Four:* The summary section, when present, was asked to speculate about the importance of the article for someone studying Korean history. This was as an experiment and sometimes it produces correct, but largely obvious observations. In other cases, however, it may make claims based on interpretations of the text that do not hold up. 

There are many other kinds of translation issues and it would be useful to have more examples posted in the "Issues" for the repository. This was an experiment to see how functional the full translation of these transcribed journals might be for careful and limited use in a teaching or research context. In the latter, especially, they definitely need to be used in close coordination with the originals (Even the original transcriptions this depends on have their own issues do not always match the original files, an issue is explored in detail in this article: Fremery, Wayne de, and Sang Hun Kim. ‘Remodeling “Creation”: The July 1922 Issue of “Kaebyŏk” Magazine’. *The Journal of Korean Studies (1979-)* 20, no. 2 (2015): 415–57. [JSTOR]( https://www.jstor.org/stable/43919327)) 

In conclusion: the translations provided here have not been reviewed for accuracy and need to be viewed with the kind of critical distance and distrust these algorithmically produced texts always deserve.

The translations were produced by Gemini 2.5 Experimental when it was free and had unlimited usage via the API. When this ended, Pyŏlgŏn'gon had to switch to having translations done by Gemini 2.0 flash, which was affordable, but of lesser quality. It struggled to understand the prompt (included in the repository as prompt.txt) and include all its components so the summary and glossary were left out. Another version of these translations with OpenAI 4o-mini will be included in the repository for anyone who wants to compare the quality of the translations. 

**Messy Data in the Translations** 

Related to the problem of translation errors, the large language model did not always return data consistently. This means that, when viewing the English version you may find the following:

- sometimes metadata is missing because it was returned in an inconsistent format
- sometimes the articles were very long, longer than the output token limits for the  large language model and these were skipped. You will then usually just see the original article instead.
- Sometimes it didn't follow the instructions on the sub-section below the main translation so you may see some variation there.

**Technical Notes** 

You may browse the raw files online here via the [site](https://yeoksayeou.github.io/), but inj the files here are not well optimized for rapid online browsing and searching. To make this as easy as possible to download and browse for anyone offline, there is no database, and raw data text files have been simply merged into data files through a build process. 

The search script loads the entire collection of articles from a journal into memory, while the browsing page loads whole issues into memory. Be patient before your first search as this may take a few seconds to load. This goes relatively fast offline, but is slower when hosted remotely. 

There is no reason this can't be easily transformed into a far faster database driven version. Anyone is of course free to make a more efficient version and fork this repository. All the scripts here were written by Claude Sonnet 3.7, with some ChatGPT 4o and Gemini 2.5.

**Shortcuts**

When viewing an article you can use the left or right arrows on your keyboard to move quickly from one article to another inside a given issue. On a mobile device you can swipe left or right to do the same. 
