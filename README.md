# Colonial Korea Periodicals Archive



This is a [site](https://yeoksayeou.github.io/) created mostly for students of history to easily browse articles of several Korean colonial period journals. 

The original journals are unlikely to be protected under any copyright, but this site only exists thanks to the transcription work of the [National Institute of Korean History](https://db.history.go.kr/) (국사편찬위원회). 

The [Database of Korean History: Modern Korea](https://db.history.go.kr/modern/) contains a huge array of important historical materials related modern Korea, including the transcriptions of articles for a number of journals, including those reposted here.

This website does not fully reproduce the rich functionality of the original website but makes it easy to download a local collection of these files for those who want to explore them quickly on your own computer. To do this, download the [repository](https://github.com/yeoksayeou/yeoksayeou.github.io) for this website and open the webpage locally on your own machine. 

Another aspect of this project is the addition of LLM English-translated versions of the articles to make these journals more accessible for students who do not know Korean, who are learning Korean but may still be early on their journey to learning hanja, or who may know Korean but find reading these Sino-Korean and Japanese language texts troublesome enough that it is helpful to have a rough English translation to refer to. 

For some of the translations here, the LLM was asked to extract a list of named entitites, a glossary of vocabulary, and a short summary. The LLM used was Gemini 2.5 for three of the journals, and Gemini 2.0 for *Pyŏlgŏn'gon*, which produced poorer quality translations.

The LLM translation exhibit all the usual problems of large language models. Be on the look out for hallucinations as well as a host of mistakes based on its incorrect translation of words from the Korean colonial context. These translations should not be quoted without first checking their accuracy and correcting them accordingly.

**Note:** You may browse the files online here via the [site](https://yeoksayeou.github.io/), but the files here are not well optimized for rapid online browsing and searching. There is no database, and raw data text files have been simply merged into data files. The search script loads the entire collection of articles from a journal into memory, while the browsing page loads whole issues into memory. This goes relatively fast offline, but is slower when hosted remotely. Anyone is of course free to make a more efficient website. All the scripts here were written by Claude Sonnet 3.7, with some ChatGPT 4o and Gemini 2.5.
