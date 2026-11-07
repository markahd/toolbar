# Writer instructions (for each chapter sub-agent)

You are writing ONE chapter of a fan-fiction audiobook. All creative decisions are made. Execute.

1. Read, in full, in this order:
   - /home/user/toolbar/kusakabe-audiobook/BRIEF.md (read Appendix A, the style reference, twice)
   - /home/user/toolbar/kusakabe-audiobook/continuity.md
   - every file in /home/user/toolbar/kusakabe-audiobook/summaries/ (summaries of earlier chapters). Also skim the previous chapter's text in /home/user/toolbar/kusakabe-audiobook/chapters/ if it exists, to match the hand and avoid repeating images.
2. Write your chapter exactly to its beats in BRIEF.md section 4. Hit every beat, canon anchor, consequence and the closing image. Do not add beats that belong to other chapters.
   - Style: Appendix A. Present tense, close third on Kusakabe, short sentences, white space, dry short inner thoughts in *italics*, sparse dialogue. Scene breaks as a line with `---`.
   - Where Appendix A already contains a passage for your chapter, you may use it as the spine, but expand it into a full chapter with fresh scenes; don't pad by repetition.
   - Word count: the bracketed target, within 10%. Count with `wc -w` on the .md and adjust before finishing. Aim for the target, not the floor.
   - Fights: a few hundred words at most, through his body. No choreography.
   - Nothing from the "Lines and images already used" list in continuity.md, except the listed motifs.
   - No childhood flashbacks, no stated morals, no therapy-speak. End on an image, action or dry thought.
   - Begin the .md with a heading: `# Chapter N. Title`.
3. Write the TTS version following BRIEF.md section 6 precisely: plain text, first line "Chapter <number in words>. <Title>." then a blank line; no asterisks, underscores, hashes, brackets, slashes, dashes used as symbols, or digits (write numbers as words; "B five F"); every scene break becomes a blank line followed by a short re-anchoring sentence; inner thoughts in their own short paragraphs, with "he thinks" added only where needed for the ear; split any sentence over about 35 words. Em dashes are discouraged; prefer commas or full stops. Text otherwise identical to the .md.
4. Files to write (exact paths):
   - /home/user/toolbar/kusakabe-audiobook/chapters/chNN.md
   - /home/user/toolbar/kusakabe-audiobook/full_book_tts/chNN_tts.txt
   - /home/user/toolbar/kusakabe-audiobook/summaries/chNN.md containing: a 150-word summary of the chapter, then a heading "Continuity updates" listing any new names, facts, and the distinctive lines, jokes and images you used (so later writers don't repeat them).
   (NN is two digits, e.g. 03.)
5. Run `python3 /home/user/toolbar/kusakabe-audiobook/scripts/check_chapter.py chNN` and fix everything it reports. Then re-read the chapter once against the quality gate in BRIEF.md section 5 and fix anything that fails.
6. Do not edit any other files. Do not commit. Reply with only: the final word count, the checker output, and one line on anything you were unsure about.
