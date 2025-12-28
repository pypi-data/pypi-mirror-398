"""
Multi-Source Wisdom System for Exarp

Provides inspirational/humorous quotes from various public domain texts
matched to project health status.

Available Sources (17 local + 4 Sefaria API):
- random: Randomly pick from any source (daily consistent)
- pistis_sophia: Gnostic mysticism (default)
- bofh: Bastard Operator From Hell (tech humor)
- tao: Tao Te Ching (balance and flow)
- art_of_war: Sun Tzu (strategy)
- stoic: Marcus Aurelius & Epictetus (resilience)
- bible: Proverbs & Ecclesiastes (wisdom)
- tao_of_programming: Tech philosophy
- murphy: Murphy's Laws (pragmatism)
- shakespeare: The Bard (drama)
- confucius: The Analects (ethics)
- kybalion: Hermetic Philosophy (mental models)     [NEW from sacred-texts.com]
- gracian: Art of Worldly Wisdom (pragmatic maxims) [NEW from sacred-texts.com]
- enochian: John Dee's mystical calls               [NEW from sacred-texts.com]

Configuration:
- EXARP_WISDOM_SOURCE=<source_name>  (default: pistis_sophia, use "random" for variety)
- EXARP_DISABLE_WISDOM=1             (disable all wisdom)
- .exarp_wisdom_config               (JSON config file)

Credits: Many texts sourced from https://sacred-texts.com/ (public domain)
"""

import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# WISDOM DATABASES BY SOURCE
# ═══════════════════════════════════════════════════════════════════════════════

WISDOM_SOURCES = {

    # ─────────────────────────────────────────────────────────────────────────────
    # BOFH - Bastard Operator From Hell (Simon Travaglia)
    # Perfect for: debugging sessions, outages, dealing with "users"
    # ─────────────────────────────────────────────────────────────────────────────
    "bofh": {
        "name": "BOFH (Bastard Operator From Hell)",
        "icon": "😈",
        "chaos": [
            {"quote": "It's not a bug, it's a feature.", "source": "BOFH Excuse Calendar", "encouragement": "Document it and ship it."},
            {"quote": "Have you tried turning it off and on again?", "source": "BOFH Classic", "encouragement": "Sometimes the classics work."},
            {"quote": "The problem exists between keyboard and chair.", "source": "BOFH Wisdom", "encouragement": "Check your assumptions."},
        ],
        "lower_aeons": [
            {"quote": "Strstrstrrstrstrstrtstrstrst", "source": "BOFH on Serial Cables", "encouragement": "Check your connections."},
            {"quote": "We don't support that. We never have. We never will.", "source": "BOFH Helpdesk", "encouragement": "Set clear boundaries."},
            {"quote": "The backup system is working perfectly. Unfortunately, the restore system isn't.", "source": "BOFH on Backups", "encouragement": "Test your recovery procedures."},
        ],
        "middle_aeons": [
            {"quote": "Users are like cattle. Sometimes you have to thin the herd.", "source": "BOFH on User Management", "encouragement": "Prioritize your support queue."},
            {"quote": "Whose fault is it? The network's, obviously.", "source": "BOFH Troubleshooting", "encouragement": "It's always DNS."},
            {"quote": "The system isn't slow, it's just contemplating.", "source": "BOFH on Performance", "encouragement": "Perception is reality."},
        ],
        "upper_aeons": [
            {"quote": "I don't have a solution, but I do admire the problem.", "source": "BOFH Philosophy", "encouragement": "Some problems are worth appreciating."},
            {"quote": "The nice thing about standards is there are so many to choose from.", "source": "BOFH on Standards", "encouragement": "Pick one and stick with it."},
            {"quote": "A user's cry for help is just noise. A server's cry for help is a priority one incident.", "source": "BOFH Priorities", "encouragement": "Know what matters."},
        ],
        "treasury": [
            {"quote": "It's not the logs that lie, it's the users.", "source": "BOFH Truth", "encouragement": "Trust but verify."},
            {"quote": "In the land of the blind, the one-eyed sysadmin is king.", "source": "BOFH Power", "encouragement": "Your expertise matters."},
            {"quote": "The server room is my happy place. No users allowed.", "source": "BOFH Zen", "encouragement": "Protect your focus time."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # TAO TE CHING - Lao Tzu
    # Perfect for: finding balance, letting go, embracing simplicity
    # ─────────────────────────────────────────────────────────────────────────────
    "tao": {
        "name": "Tao Te Ching (Lao Tzu)",
        "icon": "☯️",
        "chaos": [
            {"quote": "The journey of a thousand miles begins with a single step.", "source": "Chapter 64", "encouragement": "Start where you are."},
            {"quote": "When I let go of what I am, I become what I might be.", "source": "Chapter 22", "encouragement": "Release attachment to the old code."},
            {"quote": "Nature does not hurry, yet everything is accomplished.", "source": "Chapter 15", "encouragement": "Patience brings clarity."},
        ],
        "lower_aeons": [
            {"quote": "The soft overcomes the hard. The slow overcomes the fast.", "source": "Chapter 36", "encouragement": "Incremental progress wins."},
            {"quote": "To attain knowledge, add things every day. To attain wisdom, remove things every day.", "source": "Chapter 48", "encouragement": "Simplify."},
            {"quote": "He who knows others is wise. He who knows himself is enlightened.", "source": "Chapter 33", "encouragement": "Understand your codebase."},
        ],
        "middle_aeons": [
            {"quote": "Act without expectation.", "source": "Chapter 2", "encouragement": "Do the work for its own sake."},
            {"quote": "The Tao that can be told is not the eternal Tao.", "source": "Chapter 1", "encouragement": "Some things must be experienced."},
            {"quote": "Knowing others is intelligence; knowing yourself is true wisdom.", "source": "Chapter 33", "encouragement": "Know your strengths and limits."},
        ],
        "upper_aeons": [
            {"quote": "The Master does nothing, yet leaves nothing undone.", "source": "Chapter 48", "encouragement": "Automation is the way."},
            {"quote": "In dwelling, live close to the ground. In thinking, keep to the simple.", "source": "Chapter 8", "encouragement": "Keep it simple."},
            {"quote": "When you are content to be simply yourself, everyone will respect you.", "source": "Chapter 8", "encouragement": "Your work speaks for itself."},
        ],
        "treasury": [
            {"quote": "The Tao nourishes all things.", "source": "Chapter 51", "encouragement": "Good architecture sustains itself."},
            {"quote": "Success is as dangerous as failure. Hope is as hollow as fear.", "source": "Chapter 13", "encouragement": "Stay humble in victory."},
            {"quote": "Retire when the work is done; this is the way of heaven.", "source": "Chapter 9", "encouragement": "Know when to ship."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # ART OF WAR - Sun Tzu
    # Perfect for: strategy, planning, competitive situations
    # ─────────────────────────────────────────────────────────────────────────────
    "art_of_war": {
        "name": "The Art of War (Sun Tzu)",
        "icon": "⚔️",
        "chaos": [
            {"quote": "In the midst of chaos, there is also opportunity.", "source": "Chapter 3", "encouragement": "Find the opening."},
            {"quote": "If you know the enemy and know yourself, you need not fear the result of a hundred battles.", "source": "Chapter 3", "encouragement": "Understand the problem space."},
            {"quote": "Appear weak when you are strong, and strong when you are weak.", "source": "Chapter 1", "encouragement": "Manage expectations."},
        ],
        "lower_aeons": [
            {"quote": "The supreme art of war is to subdue the enemy without fighting.", "source": "Chapter 3", "encouragement": "Prevention beats remediation."},
            {"quote": "Opportunities multiply as they are seized.", "source": "Chapter 5", "encouragement": "Momentum builds momentum."},
            {"quote": "Let your plans be dark and impenetrable as night.", "source": "Chapter 7", "encouragement": "Keep competitive advantages close."},
        ],
        "middle_aeons": [
            {"quote": "Strategy without tactics is the slowest route to victory.", "source": "Chapter 6", "encouragement": "Plan and execute."},
            {"quote": "The quality of decision is like the well-timed swoop of a falcon.", "source": "Chapter 5", "encouragement": "Act decisively."},
            {"quote": "Move swift as the Wind and closely-formed as the Wood.", "source": "Chapter 7", "encouragement": "Balance speed and stability."},
        ],
        "upper_aeons": [
            {"quote": "To know your Enemy, you must become your Enemy.", "source": "Chapter 3", "encouragement": "Think like your users."},
            {"quote": "The greatest victory is that which requires no battle.", "source": "Chapter 3", "encouragement": "Design prevents bugs."},
            {"quote": "He will win who knows when to fight and when not to fight.", "source": "Chapter 3", "encouragement": "Pick your battles."},
        ],
        "treasury": [
            {"quote": "Victorious warriors win first and then go to war.", "source": "Chapter 4", "encouragement": "Plan before you code."},
            {"quote": "There are not more than five musical notes, yet their combinations give rise to more melodies than can ever be heard.", "source": "Chapter 5", "encouragement": "Simple primitives, infinite possibilities."},
            {"quote": "The whole secret lies in confusing the enemy.", "source": "Chapter 6", "encouragement": "Complexity is the enemy of security."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # STOICS - Marcus Aurelius & Epictetus
    # Perfect for: dealing with adversity, maintaining focus, resilience
    # ─────────────────────────────────────────────────────────────────────────────
    "stoic": {
        "name": "Stoic Philosophers",
        "icon": "🏛️",
        "chaos": [
            {"quote": "The impediment to action advances action. What stands in the way becomes the way.", "source": "Marcus Aurelius, Meditations", "encouragement": "Obstacles are opportunities."},
            {"quote": "It is not things that disturb us, but our judgments about things.", "source": "Epictetus, Enchiridion", "encouragement": "Change your perspective."},
            {"quote": "You have power over your mind, not outside events. Realize this, and you will find strength.", "source": "Marcus Aurelius, Meditations", "encouragement": "Focus on what you control."},
        ],
        "lower_aeons": [
            {"quote": "First say to yourself what you would be; and then do what you have to do.", "source": "Epictetus, Discourses", "encouragement": "Define then execute."},
            {"quote": "No man is free who is not master of himself.", "source": "Epictetus, Discourses", "encouragement": "Discipline equals freedom."},
            {"quote": "Waste no more time arguing what a good man should be. Be one.", "source": "Marcus Aurelius, Meditations", "encouragement": "Ship the code."},
        ],
        "middle_aeons": [
            {"quote": "The best revenge is not to be like your enemy.", "source": "Marcus Aurelius, Meditations", "encouragement": "Rise above."},
            {"quote": "He suffers more than necessary, who suffers before it is necessary.", "source": "Seneca, Letters", "encouragement": "Don't pre-worry."},
            {"quote": "If it is not right, do not do it; if it is not true, do not say it.", "source": "Marcus Aurelius, Meditations", "encouragement": "Maintain integrity."},
        ],
        "upper_aeons": [
            {"quote": "The happiness of your life depends upon the quality of your thoughts.", "source": "Marcus Aurelius, Meditations", "encouragement": "Think clearly."},
            {"quote": "We suffer more in imagination than in reality.", "source": "Seneca, Letters", "encouragement": "Most fears never materialize."},
            {"quote": "Difficulties strengthen the mind, as labor does the body.", "source": "Seneca, Letters", "encouragement": "Challenges build skill."},
        ],
        "treasury": [
            {"quote": "Very little is needed to make a happy life.", "source": "Marcus Aurelius, Meditations", "encouragement": "Simplicity is power."},
            {"quote": "How much time he gains who does not look to see what his neighbor says or does.", "source": "Marcus Aurelius, Meditations", "encouragement": "Focus on your work."},
            {"quote": "Accept the things to which fate binds you, and love the people with whom fate brings you together.", "source": "Marcus Aurelius, Meditations", "encouragement": "Embrace your team."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # BIBLE - Proverbs & Ecclesiastes (KJV - Public Domain)
    # Perfect for: wisdom about work, humility, perseverance
    # ─────────────────────────────────────────────────────────────────────────────
    "bible": {
        "name": "Bible (Proverbs & Ecclesiastes)",
        "icon": "📖",
        "chaos": [
            {"quote": "For everything there is a season, and a time for every matter under heaven.", "source": "Ecclesiastes 3:1", "encouragement": "This too shall pass."},
            {"quote": "Pride goes before destruction, and a haughty spirit before a fall.", "source": "Proverbs 16:18", "encouragement": "Stay humble in debugging."},
            {"quote": "Where there is no vision, the people perish.", "source": "Proverbs 29:18", "encouragement": "Define your goals."},
        ],
        "lower_aeons": [
            {"quote": "The beginning of wisdom is this: Get wisdom, and whatever you get, get insight.", "source": "Proverbs 4:7", "encouragement": "Learn from the error logs."},
            {"quote": "A soft answer turns away wrath, but a harsh word stirs up anger.", "source": "Proverbs 15:1", "encouragement": "Be gentle in code reviews."},
            {"quote": "Commit your work to the Lord, and your plans will be established.", "source": "Proverbs 16:3", "encouragement": "Do good work, trust the process."},
        ],
        "middle_aeons": [
            {"quote": "The hand of the diligent will rule, while the slothful will be put to forced labor.", "source": "Proverbs 12:24", "encouragement": "Consistency wins."},
            {"quote": "Better is a little with righteousness than great revenues with injustice.", "source": "Proverbs 16:8", "encouragement": "Quality over quantity."},
            {"quote": "The heart of the discerning acquires knowledge; the ears of the wise seek it out.", "source": "Proverbs 18:15", "encouragement": "Keep learning."},
        ],
        "upper_aeons": [
            {"quote": "Whatever your hand finds to do, do it with all your might.", "source": "Ecclesiastes 9:10", "encouragement": "Give full effort."},
            {"quote": "Two are better than one, because they have a good reward for their toil.", "source": "Ecclesiastes 4:9", "encouragement": "Collaborate."},
            {"quote": "A good name is to be chosen rather than great riches.", "source": "Proverbs 22:1", "encouragement": "Reputation matters."},
        ],
        "treasury": [
            {"quote": "She looks well to the ways of her household and does not eat the bread of idleness.", "source": "Proverbs 31:27", "encouragement": "Maintain vigilance."},
            {"quote": "Let another praise you, and not your own mouth; a stranger, and not your own lips.", "source": "Proverbs 27:2", "encouragement": "Let your work speak."},
            {"quote": "The end of a matter is better than its beginning, and patience is better than pride.", "source": "Ecclesiastes 7:8", "encouragement": "You've earned this."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # TAO OF PROGRAMMING - Geoffrey James (1987)
    # Perfect for: coding philosophy, programmer wisdom
    # ─────────────────────────────────────────────────────────────────────────────
    "tao_of_programming": {
        "name": "The Tao of Programming",
        "icon": "💻",
        "chaos": [
            {"quote": "A program should be light and agile, its subroutines connected like pearls on a string.", "source": "Book 4", "encouragement": "Strive for elegance."},
            {"quote": "There is a time for debugging and a time for coding. Do not confuse the two.", "source": "Book 2", "encouragement": "Separate concerns."},
            {"quote": "Though a program be but three lines long, someday it will have to be maintained.", "source": "Book 4", "encouragement": "Write for the future."},
        ],
        "lower_aeons": [
            {"quote": "A well-written program is its own heaven; a poorly-written program is its own hell.", "source": "Book 1", "encouragement": "Quality is its own reward."},
            {"quote": "Without the wind, the grass does not move. Without software, hardware is useless.", "source": "Book 1", "encouragement": "Your code matters."},
            {"quote": "The wise programmer is told about Tao and follows it. The average programmer is told about Tao and searches for it.", "source": "Book 1", "encouragement": "Learn by doing."},
        ],
        "middle_aeons": [
            {"quote": "When managers make commitments, game programs are ignored. When programmers make commitments, corporate programs are made.", "source": "Book 3", "encouragement": "Promises shape reality."},
            {"quote": "A novice asked the Master: 'What is the true meaning of programming?' The Master replied: 'Eat when you are hungry. Sleep when you are tired. Code when you are ready.'", "source": "Book 2", "encouragement": "Respect your rhythms."},
            {"quote": "The best software is invisible.", "source": "Book 4", "encouragement": "Users should see results, not complexity."},
        ],
        "upper_aeons": [
            {"quote": "There was once a programmer who worked upon microprocessors. 'Look at how well off I am here,' he said. 'I have the smallest office, the smallest desk, and I must sit on the floor.'", "source": "Book 8", "encouragement": "Constraints breed creativity."},
            {"quote": "The Master said: 'A well-designed system needs no manual.'", "source": "Book 5", "encouragement": "Intuitive beats documented."},
            {"quote": "Let the programmers be many and the managers few -- then all will be productive.", "source": "Book 7", "encouragement": "Trust the doers."},
        ],
        "treasury": [
            {"quote": "After three days without programming, life becomes meaningless.", "source": "Book 2", "encouragement": "You're in your element."},
            {"quote": "The Master said: 'That program is good that has few bugs.'", "source": "Book 4", "encouragement": "Simplicity prevails."},
            {"quote": "A master programmer passed a novice programmer one day. The master noted the novice's preoccupation with a hand-held game. 'Excuse me,' he said, 'may I examine it?' The novice handed it to him. 'I see that the game requires you to push buttons to make helicopters and tanks shoot each other,' said the master. 'That is correct,' said the novice. 'But it has no purpose.' The master threw the game to the ground and crushed it under his heel. 'Neither does your code,' said the master. The novice was enlightened.", "source": "Book 6", "encouragement": "Purpose over pixels."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # MURPHY'S LAW - Various
    # Perfect for: testing, releases, estimates, risk management
    # ─────────────────────────────────────────────────────────────────────────────
    "murphy": {
        "name": "Murphy's Laws",
        "icon": "🎲",
        "chaos": [
            {"quote": "Anything that can go wrong will go wrong.", "source": "Murphy's Law", "encouragement": "Plan for failure."},
            {"quote": "Left to themselves, things tend to go from bad to worse.", "source": "Murphy's Law (Corollary)", "encouragement": "Don't leave things."},
            {"quote": "If there is a possibility of several things going wrong, the one that will cause the most damage will be the one to go wrong.", "source": "Murphy's Law (Extreme)", "encouragement": "Fix the critical path first."},
        ],
        "lower_aeons": [
            {"quote": "Nothing is as easy as it looks.", "source": "Murphy's Law", "encouragement": "Pad your estimates."},
            {"quote": "Everything takes longer than you think.", "source": "Murphy's Law", "encouragement": "Double it."},
            {"quote": "Every solution breeds new problems.", "source": "Murphy's Law", "encouragement": "Think second-order effects."},
        ],
        "middle_aeons": [
            {"quote": "It is impossible to make anything foolproof because fools are so ingenious.", "source": "Murphy's Law", "encouragement": "Test with real users."},
            {"quote": "Hofstadter's Law: It always takes longer than you expect, even when you take into account Hofstadter's Law.", "source": "Douglas Hofstadter", "encouragement": "Accept recursive delays."},
            {"quote": "The first 90% of the code accounts for the first 90% of the development time. The remaining 10% of the code accounts for the other 90%.", "source": "Tom Cargill", "encouragement": "The last mile is the hardest."},
        ],
        "upper_aeons": [
            {"quote": "If you make something idiot-proof, someone will make a better idiot.", "source": "Murphy's Law", "encouragement": "Keep iterating."},
            {"quote": "The light at the end of the tunnel is just the light of an oncoming train.", "source": "Murphy's Law", "encouragement": "Stay vigilant near completion."},
            {"quote": "For every action, there is an equal and opposite criticism.", "source": "Harrison's Postulate", "encouragement": "Ship anyway."},
        ],
        "treasury": [
            {"quote": "If Murphy's Law can go wrong, it will.", "source": "Murphy's Meta-Law", "encouragement": "Even pessimism has limits."},
            {"quote": "The primary function of the design engineer is to make things difficult for the fabricator and impossible for the serviceman.", "source": "Murphy's Law", "encouragement": "Write docs for future you."},
            {"quote": "Blessed is he who expects nothing, for he shall not be disappointed.", "source": "Murphy's Blessing", "encouragement": "Exceed low expectations."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # SHAKESPEARE - The Bard
    # Perfect for: leadership, conflict, ambition, human nature
    # ─────────────────────────────────────────────────────────────────────────────
    "shakespeare": {
        "name": "William Shakespeare",
        "icon": "🎭",
        "chaos": [
            {"quote": "Hell is empty and all the devils are here.", "source": "The Tempest, Act 1", "encouragement": "Face the chaos."},
            {"quote": "When sorrows come, they come not single spies, but in battalions.", "source": "Hamlet, Act 4", "encouragement": "Problems cluster."},
            {"quote": "The fault, dear Brutus, is not in our stars, but in ourselves.", "source": "Julius Caesar, Act 1", "encouragement": "Take ownership."},
        ],
        "lower_aeons": [
            {"quote": "There is nothing either good or bad, but thinking makes it so.", "source": "Hamlet, Act 2", "encouragement": "Perspective is everything."},
            {"quote": "All things are ready, if our minds be so.", "source": "Henry V, Act 4", "encouragement": "Mindset determines outcome."},
            {"quote": "What's past is prologue.", "source": "The Tempest, Act 2", "encouragement": "Learn and move forward."},
        ],
        "middle_aeons": [
            {"quote": "Though she be but little, she is fierce.", "source": "A Midsummer Night's Dream, Act 3", "encouragement": "Small teams can be powerful."},
            {"quote": "Love all, trust a few, do wrong to none.", "source": "All's Well That Ends Well, Act 1", "encouragement": "Build trust carefully."},
            {"quote": "The better part of valour is discretion.", "source": "Henry IV Part 1, Act 5", "encouragement": "Know when to retreat."},
        ],
        "upper_aeons": [
            {"quote": "Some are born great, some achieve greatness, and some have greatness thrust upon them.", "source": "Twelfth Night, Act 2", "encouragement": "Rise to the occasion."},
            {"quote": "We know what we are, but know not what we may be.", "source": "Hamlet, Act 4", "encouragement": "Potential exceeds perception."},
            {"quote": "To thine own self be true.", "source": "Hamlet, Act 1", "encouragement": "Maintain your principles."},
        ],
        "treasury": [
            {"quote": "All's well that ends well.", "source": "All's Well That Ends Well", "encouragement": "Outcomes matter."},
            {"quote": "Our doubts are traitors, and make us lose the good we oft might win, by fearing to attempt.", "source": "Measure for Measure, Act 1", "encouragement": "Ship it."},
            {"quote": "The web of our life is of a mingled yarn, good and ill together.", "source": "All's Well That Ends Well, Act 4", "encouragement": "Embrace complexity."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # CONFUCIUS - The Analects
    # Perfect for: ethics, mastery, team dynamics, teaching
    # ─────────────────────────────────────────────────────────────────────────────
    "confucius": {
        "name": "Confucius (The Analects)",
        "icon": "🎓",
        "chaos": [
            {"quote": "Our greatest glory is not in never falling, but in rising every time we fall.", "source": "Analects", "encouragement": "Get back up."},
            {"quote": "The man who moves a mountain begins by carrying away small stones.", "source": "Analects", "encouragement": "Start small."},
            {"quote": "When it is obvious that the goals cannot be reached, don't adjust the goals, adjust the action steps.", "source": "Analects", "encouragement": "Iterate on approach."},
        ],
        "lower_aeons": [
            {"quote": "It does not matter how slowly you go as long as you do not stop.", "source": "Analects", "encouragement": "Persistence wins."},
            {"quote": "I hear and I forget. I see and I remember. I do and I understand.", "source": "Analects", "encouragement": "Learn by doing."},
            {"quote": "Real knowledge is to know the extent of one's ignorance.", "source": "Analects", "encouragement": "Acknowledge gaps."},
        ],
        "middle_aeons": [
            {"quote": "The superior man is modest in his speech, but exceeds in his actions.", "source": "Analects", "encouragement": "Let work speak."},
            {"quote": "By three methods we may learn wisdom: by reflection, which is noblest; by imitation, which is easiest; and by experience, which is the bitterest.", "source": "Analects", "encouragement": "All learning is valid."},
            {"quote": "Choose a job you love, and you will never have to work a day in your life.", "source": "Analects", "encouragement": "Passion sustains."},
        ],
        "upper_aeons": [
            {"quote": "The man of virtue makes the difficulty to be overcome his first interest; success only comes later.", "source": "Analects", "encouragement": "Process over outcome."},
            {"quote": "If you think in terms of a year, plant a seed; if in terms of ten years, plant trees; if in terms of 100 years, teach the people.", "source": "Analects", "encouragement": "Invest in documentation."},
            {"quote": "The more man meditates upon good thoughts, the better will be his world and the world at large.", "source": "Analects", "encouragement": "Positive thinking matters."},
        ],
        "treasury": [
            {"quote": "What you do not want done to yourself, do not do to others.", "source": "Analects", "encouragement": "Write code you'd want to maintain."},
            {"quote": "Only the wisest and stupidest of men never change.", "source": "Analects", "encouragement": "Stay adaptable."},
            {"quote": "When you see a worthy person, endeavor to emulate them.", "source": "Analects", "encouragement": "Learn from the best."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # THE KYBALION - Hermetic Philosophy (Three Initiates, 1908)
    # Source: https://sacred-texts.com/eso/kyb/index.htm (Public Domain)
    # Perfect for: understanding systems, mental models, cause and effect
    # ─────────────────────────────────────────────────────────────────────────────
    "kybalion": {
        "name": "The Kybalion (Hermetic Philosophy)",
        "icon": "⚗️",
        "chaos": [
            {"quote": "THE ALL is MIND; The Universe is Mental.", "source": "Principle of Mentalism", "encouragement": "Your mental model shapes your code."},
            {"quote": "As above, so below; as below, so above.", "source": "Principle of Correspondence", "encouragement": "Patterns repeat at every scale."},
            {"quote": "Nothing rests; everything moves; everything vibrates.", "source": "Principle of Vibration", "encouragement": "Change is the only constant."},
        ],
        "lower_aeons": [
            {"quote": "Everything is Dual; everything has poles; everything has its pair of opposites.", "source": "Principle of Polarity", "encouragement": "Bugs and features are matters of degree."},
            {"quote": "Everything flows, out and in; everything has its tides.", "source": "Principle of Rhythm", "encouragement": "Sprints have natural rhythms."},
            {"quote": "The Principles of Truth are Seven; he who knows these, understandingly, possesses the Magic Key.", "source": "The Kybalion", "encouragement": "Master the fundamentals."},
        ],
        "middle_aeons": [
            {"quote": "Every Cause has its Effect; every Effect has its Cause.", "source": "Principle of Cause and Effect", "encouragement": "Debug systematically."},
            {"quote": "Gender is in everything; everything has its Masculine and Feminine Principles.", "source": "Principle of Gender", "encouragement": "Balance creation and refinement."},
            {"quote": "The half-wise, recognizing the unreality of the Universe, imagine that they may defy its Laws. Such are vain and presumptuous fools.", "source": "The Kybalion", "encouragement": "Respect the constraints."},
        ],
        "upper_aeons": [
            {"quote": "Mind may be transmuted, from state to state; degree to degree; pole to pole; vibration to vibration.", "source": "The Kybalion", "encouragement": "Refactoring transforms understanding."},
            {"quote": "The wise ones serve on the higher planes, but rule on the lower.", "source": "The Kybalion", "encouragement": "Lead by example, delegate wisely."},
            {"quote": "Nothing escapes the Principle of Cause and Effect, but there are many Planes of Causation.", "source": "The Kybalion", "encouragement": "Look for root causes."},
        ],
        "treasury": [
            {"quote": "The lips of Wisdom are closed, except to the ears of Understanding.", "source": "The Kybalion", "encouragement": "Documentation for those who seek."},
            {"quote": "Where falls the footsteps of the Master, the ears of those ready for his Teaching open wide.", "source": "The Kybalion", "encouragement": "Teach those who are ready."},
            {"quote": "When the ears of the student are ready to hear, then cometh the lips to fill them with Wisdom.", "source": "The Kybalion", "encouragement": "The learner appears when ready."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # THE ART OF WORLDLY WISDOM - Baltasar Gracián (1647)
    # Source: https://sacred-texts.com/eso/aww/index.htm (Public Domain)
    # Perfect for: pragmatic wisdom, strategy, dealing with people, career
    # ─────────────────────────────────────────────────────────────────────────────
    "gracian": {
        "name": "Art of Worldly Wisdom (Gracián)",
        "icon": "🎭",
        "chaos": [
            {"quote": "Never open the door to a lesser evil, for other and greater ones invariably slink in after it.", "source": "Maxim 76", "encouragement": "Fix the bug now, not later."},
            {"quote": "Know how to ask. There is nothing more difficult for some, nothing easier for others.", "source": "Maxim 213", "encouragement": "Ask for help early."},
            {"quote": "Begin with another's to end with your own.", "source": "Maxim 144", "encouragement": "Understand requirements first."},
        ],
        "lower_aeons": [
            {"quote": "A single lie destroys a whole reputation for integrity.", "source": "Maxim 181", "encouragement": "Honesty in commit messages."},
            {"quote": "Know how to make use of stupidity: The wisest man plays this card at times.", "source": "Maxim 240", "encouragement": "Rubber duck debugging works."},
            {"quote": "Never contend with a man who has nothing to lose.", "source": "Maxim 172", "encouragement": "Pick your battles."},
        ],
        "middle_aeons": [
            {"quote": "Think with the few and speak with the many.", "source": "Maxim 43", "encouragement": "Design privately, communicate widely."},
            {"quote": "The things we remember best are those better forgotten.", "source": "Maxim 262", "encouragement": "Document the weird edge cases."},
            {"quote": "Do not wait till you are a sinking sun.", "source": "Maxim 110", "encouragement": "Know when to refactor."},
        ],
        "upper_aeons": [
            {"quote": "Have knowledge and courage, they make for greatness.", "source": "Maxim 185", "encouragement": "Learn continuously, ship boldly."},
            {"quote": "Know how to withdraw. If it is a great lesson in life to know how to deny, it is a still greater to know how to deny oneself.", "source": "Maxim 33", "encouragement": "Say no to scope creep."},
            {"quote": "The sole advantage of power is that you can do more good.", "source": "Maxim 286", "encouragement": "Use your influence wisely."},
        ],
        "treasury": [
            {"quote": "Attempt easy tasks as if they were difficult, and difficult as if they were easy.", "source": "Maxim 204", "encouragement": "Respect all code equally."},
            {"quote": "Fortune pays you sometimes for the intensity of her favors by the shortness of their duration.", "source": "Maxim 38", "encouragement": "Enjoy the wins, prepare for challenges."},
            {"quote": "Leave off hungry. One ought to remove even from the nectar of pleasure the cup from the lips.", "source": "Maxim 60", "encouragement": "Ship before perfect."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # ENOCHIAN - Mystical Calls of John Dee (1580s)
    # Source: https://sacred-texts.com/eso/enoch/index.htm (Public Domain)
    # Perfect for: invoking focus, ceremonial starts, mystical debugging
    # ─────────────────────────────────────────────────────────────────────────────
    "enochian": {
        "name": "Enochian Mysticism (John Dee)",
        "icon": "🔮",
        "chaos": [
            {"quote": "I reign over you, saith the God of Justice, in power exalted above the firmaments of wrath.", "source": "First Call", "encouragement": "Take command of the chaos."},
            {"quote": "Can the wings of the winds understand your voices of wonder?", "source": "First Call", "encouragement": "Communicate with precision."},
            {"quote": "Move and show yourselves! Open the mysteries of your creation!", "source": "First Call", "encouragement": "Debug with intention."},
        ],
        "lower_aeons": [
            {"quote": "The spirits of the fourth angle are nine, mighty in the firmament of waters.", "source": "Fourth Call", "encouragement": "Structure brings power."},
            {"quote": "Arise! Move! and appear before the covenant of his mouth.", "source": "Second Call", "encouragement": "Honor your commitments."},
            {"quote": "Visit us in peace and comfort. Conclude us receivers of your mysteries.", "source": "Calls", "encouragement": "Seek understanding calmly."},
        ],
        "middle_aeons": [
            {"quote": "Behold the face of your God, the beginning of comfort.", "source": "Third Call", "encouragement": "Find joy in the work."},
            {"quote": "Whose works shall be a song of honor.", "source": "Calls", "encouragement": "Take pride in clean code."},
            {"quote": "Move therefore, and show yourselves!", "source": "Calls", "encouragement": "Make your intentions visible."},
        ],
        "upper_aeons": [
            {"quote": "Gather up your garments, and harken unto my voice.", "source": "Calls", "encouragement": "Prepare for deployment."},
            {"quote": "In power and presence come to us.", "source": "Calls", "encouragement": "Bring your full attention."},
            {"quote": "Whose voices the winged creatures speak.", "source": "Calls", "encouragement": "Let your work speak for itself."},
        ],
        "treasury": [
            {"quote": "I am your God, that hath created the world.", "source": "Calls", "encouragement": "You are the creator of your domain."},
            {"quote": "Arise, saith the First. Move therefore unto his servants.", "source": "Calls", "encouragement": "Lead by action."},
            {"quote": "The work is finished.", "source": "Calls", "encouragement": "Ship it."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # REBBE - Chassidic/Rabbinical Wisdom
    # Source: Sefaria.org API + curated Chassidic teachings
    # Perfect for: ethical guidance, righteous conduct, spiritual debugging
    # Language: Hebrew support via Sefaria API
    # ─────────────────────────────────────────────────────────────────────────────
    "rebbe": {
        "name": "הרבי (The Rebbe) - Chassidic Wisdom",
        "icon": "🕎",
        "language": "hebrew",
        "sefaria_source": "pirkei_avot",  # Primary Sefaria source
        "chaos": [
            {"quote": "אם אין אני לי מי לי, וכשאני לעצמי מה אני, ואם לא עכשיו אימתי (If I am not for myself, who will be for me? And if I am only for myself, what am I? And if not now, when?)", "source": "Pirkei Avot 1:14", "encouragement": "Take responsibility now."},
            {"quote": "לא עליך המלאכה לגמור, ולא אתה בן חורין ליבטל ממנה (You are not obligated to complete the work, but neither are you free to desist from it.)", "source": "Pirkei Avot 2:16", "encouragement": "Start where you are."},
            {"quote": "בִּמְקוֹם שֶׁאֵין אֲנָשִׁים, הִשְׁתַּדֵּל לִהְיוֹת אִישׁ (In a place where there are no men, strive to be a man.)", "source": "Pirkei Avot 2:5", "encouragement": "Lead when others won't."},
        ],
        "lower_aeons": [
            {"quote": "עֲשֵׂה לְךָ רַב, וּקְנֵה לְךָ חָבֵר (Make for yourself a teacher, and acquire for yourself a friend.)", "source": "Pirkei Avot 1:6", "encouragement": "Seek mentorship and collaboration."},
            {"quote": "אַל תִּסְתַּכֵּל בַּקַּנְקַן, אֶלָּא בְּמַה שֶּׁיֶּשׁ בּוֹ (Do not look at the container, but at what is in it.)", "source": "Pirkei Avot 4:20", "encouragement": "Judge code by quality, not appearance."},
            {"quote": "הֱוֵי מְקַבֵּל אֶת כָּל הָאָדָם בְּסֵבֶר פָּנִים יָפוֹת (Greet every person with a pleasant countenance.)", "source": "Pirkei Avot 1:15", "encouragement": "Kindness in code review."},
        ],
        "middle_aeons": [
            {"quote": "אֵיזֶהוּ חָכָם, הַלּוֹמֵד מִכָּל אָדָם (Who is wise? One who learns from every person.)", "source": "Pirkei Avot 4:1", "encouragement": "Every bug is a teacher."},
            {"quote": "אֵיזֶהוּ גִבּוֹר, הַכּוֹבֵשׁ אֶת יִצְרוֹ (Who is mighty? One who conquers their inclination.)", "source": "Pirkei Avot 4:1", "encouragement": "Master your impulses."},
            {"quote": "יְהִי כְבוֹד חֲבֵרְךָ חָבִיב עָלֶיךָ כְּשֶׁלָּךְ (Let your friend's honor be as dear to you as your own.)", "source": "Pirkei Avot 2:10", "encouragement": "Respect your teammates."},
        ],
        "upper_aeons": [
            {"quote": "אַל תְּהִי בָז לְכָל אָדָם, וְאַל תְּהִי מַפְלִיג לְכָל דָּבָר (Despise no one and consider nothing impossible.)", "source": "Pirkei Avot 4:3", "encouragement": "Everything is achievable."},
            {"quote": "הֱוֵי עַז כַּנָּמֵר, וְקַל כַּנֶּשֶׁר, וְרָץ כַּצְּבִי, וְגִבּוֹר כָּאֲרִי (Be bold as a leopard, light as an eagle, swift as a deer, and strong as a lion.)", "source": "Pirkei Avot 5:20", "encouragement": "Bring your full energy."},
            {"quote": "דַּע מֵאַיִן בָּאתָ, וּלְאָן אַתָּה הוֹלֵךְ (Know from where you came, and to where you are going.)", "source": "Pirkei Avot 3:1", "encouragement": "Understand your path."},
        ],
        "treasury": [
            {"quote": "עַל שְׁלֹשָׁה דְּבָרִים הָעוֹלָם עוֹמֵד, עַל הַתּוֹרָה וְעַל הָעֲבוֹדָה וְעַל גְּמִילוּת חֲסָדִים (The world stands on three things: Torah, service, and acts of kindness.)", "source": "Pirkei Avot 1:2", "encouragement": "Foundation of all work."},
            {"quote": "כָּל יִשְׂרָאֵל יֵשׁ לָהֶם חֵלֶק לָעוֹלָם הַבָּא (All Israel have a share in the World to Come.)", "source": "Sanhedrin 90a", "encouragement": "Your work matters eternally."},
            {"quote": "תִּקּוּן עוֹלָם (Repair the world)", "source": "Jewish Teaching", "encouragement": "Your code can heal."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # TZADDIK - The Righteous One
    # Source: Sefaria.org API + Mussar teachings
    # Perfect for: perseverance, ethics, staying on the right path
    # Language: Hebrew support via Sefaria API
    # ─────────────────────────────────────────────────────────────────────────────
    "tzaddik": {
        "name": "הצדיק (The Tzaddik) - Path of Righteousness",
        "icon": "✡️",
        "language": "hebrew",
        "sefaria_source": "proverbs",  # Primary Sefaria source
        "chaos": [
            {"quote": "כִּי שֶׁבַע יִפּוֹל צַדִּיק וָקָם (For a righteous man falls seven times and rises.)", "source": "Proverbs 24:16", "encouragement": "Rise after every failure."},
            {"quote": "בְּטַח אֶל ה' בְּכָל לִבֶּךָ (Trust in the Lord with all your heart.)", "source": "Proverbs 3:5", "encouragement": "Trust the process."},
            {"quote": "רֵאשִׁית חָכְמָה יִרְאַת ה' (The fear of the Lord is the beginning of wisdom.)", "source": "Proverbs 9:10", "encouragement": "Respect the fundamentals."},
        ],
        "lower_aeons": [
            {"quote": "דֶּרֶךְ חַיִּים תּוֹכְחוֹת מוּסָר (The reproofs of discipline are the way of life.)", "source": "Proverbs 6:23", "encouragement": "Corrections are blessings."},
            {"quote": "לֵב שָׂמֵחַ יֵיטִב גֵּהָה (A joyful heart is good medicine.)", "source": "Proverbs 17:22", "encouragement": "Joy fuels productivity."},
            {"quote": "בַּרְזֶל בְּבַרְזֶל יָחַד (Iron sharpens iron.)", "source": "Proverbs 27:17", "encouragement": "Pair programming."},
        ],
        "middle_aeons": [
            {"quote": "מַעֲנֶה רַךְ יָשִׁיב חֵמָה (A soft answer turns away wrath.)", "source": "Proverbs 15:1", "encouragement": "Gentle code reviews."},
            {"quote": "טוֹב שֵׁם מִשֶּׁמֶן טוֹב (A good name is better than precious oil.)", "source": "Ecclesiastes 7:1", "encouragement": "Reputation matters."},
            {"quote": "עֵת לַחֲשׁוֹת וְעֵת לְדַבֵּר (A time to keep silence and a time to speak.)", "source": "Ecclesiastes 3:7", "encouragement": "Know when to code vs. communicate."},
        ],
        "upper_aeons": [
            {"quote": "טוֹבִים הַשְּׁנַיִם מִן הָאֶחָד (Two are better than one.)", "source": "Ecclesiastes 4:9", "encouragement": "Teamwork multiplies."},
            {"quote": "הַסֹּף דָּבָר הַכֹּל נִשְׁמָע (The conclusion of the matter; all has been heard.)", "source": "Ecclesiastes 12:13", "encouragement": "Ship it."},
            {"quote": "לַכֹּל זְמָן (There is a time for everything.)", "source": "Ecclesiastes 3:1", "encouragement": "Trust the timeline."},
        ],
        "treasury": [
            {"quote": "עֹשֶׂה צְדָקָה בְכָל עֵת (One who does righteousness at all times.)", "source": "Psalms 106:3", "encouragement": "Consistent excellence."},
            {"quote": "צַדִּיק כַּתָּמָר יִפְרָח (The righteous shall flourish like a palm tree.)", "source": "Psalms 92:13", "encouragement": "Growth is inevitable."},
            {"quote": "אוֹר זָרֻעַ לַצַּדִּיק (Light is sown for the righteous.)", "source": "Psalms 97:11", "encouragement": "Light awaits."},
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # CHACHAM - The Sage
    # Source: Sefaria.org API + Talmudic wisdom
    # Perfect for: deep analysis, understanding, learning from tradition
    # Language: Hebrew support via Sefaria API
    # ─────────────────────────────────────────────────────────────────────────────
    "chacham": {
        "name": "החכם (The Chacham) - Sage Wisdom",
        "icon": "📜",
        "language": "hebrew",
        "sefaria_source": "pirkei_avot",  # Primary Sefaria source
        "chaos": [
            {"quote": "לֹא הַבַּיְשָׁן לָמֵד (The shy person cannot learn.)", "source": "Pirkei Avot 2:5", "encouragement": "Ask questions boldly."},
            {"quote": "עֲשֵׂה תוֹרָתְךָ קֶבַע (Make your Torah study fixed.)", "source": "Pirkei Avot 1:15", "encouragement": "Consistent learning."},
            {"quote": "הַכֹּל צָפוּי וְהָרְשׁוּת נְתוּנָה (All is foreseen, yet freedom of choice is granted.)", "source": "Pirkei Avot 3:15", "encouragement": "Plan but adapt."},
        ],
        "lower_aeons": [
            {"quote": "אֵין הַקַּפְדָּן מְלַמֵּד (An impatient person cannot teach.)", "source": "Pirkei Avot 2:5", "encouragement": "Patience in mentoring."},
            {"quote": "שְׁתֹק וּלְמַד (Be silent and learn.)", "source": "Pirkei Avot 1:17", "encouragement": "Listen more."},
            {"quote": "מַרְבֶּה תּוֹרָה מַרְבֶּה חַיִּים (More Torah, more life.)", "source": "Pirkei Avot 2:7", "encouragement": "Knowledge extends capability."},
        ],
        "middle_aeons": [
            {"quote": "לֹא הַמִּדְרָשׁ הָעִקָּר אֶלָּא הַמַּעֲשֶׂה (Not study but practice is the main thing.)", "source": "Pirkei Avot 1:17", "encouragement": "Ship working code."},
            {"quote": "הוּא הָיָה אוֹמֵר: אַל תִּסְתַּכֵּל בַּקַּנְקַן (He used to say: Don't look at the vessel.)", "source": "Pirkei Avot 4:20", "encouragement": "Substance over style."},
            {"quote": "אִם אֵין קֶמַח, אֵין תּוֹרָה (If there is no flour, there is no Torah.)", "source": "Pirkei Avot 3:17", "encouragement": "Basics first."},
        ],
        "upper_aeons": [
            {"quote": "טוֹבָה שָׁעָה אַחַת בִּתְשׁוּבָה וּמַעֲשִׂים טוֹבִים בָּעוֹלָם הַזֶּה (Better one hour of repentance and good deeds in this world.)", "source": "Pirkei Avot 4:17", "encouragement": "Every moment counts."},
            {"quote": "דַּע מַה שֶּׁתָּשִׁיב לְאֶפִּיקוֹרוֹס (Know what to answer a skeptic.)", "source": "Pirkei Avot 2:14", "encouragement": "Prepare your defense."},
            {"quote": "כָּל מַחֲלֹקֶת שֶׁהִיא לְשֵׁם שָׁמַיִם (Every controversy for the sake of Heaven.)", "source": "Pirkei Avot 5:17", "encouragement": "Healthy debate builds."},
        ],
        "treasury": [
            {"quote": "תַּלְמוּד תּוֹרָה כְּנֶגֶד כֻּלָּם (Torah study is equivalent to all.)", "source": "Pirkei Avot 1:1", "encouragement": "Learning is supreme."},
            {"quote": "עָתִיד אָדָם לִתֵּן דִּין וְחֶשְׁבּוֹן (A person will give an accounting.)", "source": "Pirkei Avot 3:1", "encouragement": "Code responsibly."},
            {"quote": "חוֹתָמוֹ שֶׁל הַקָּדוֹשׁ בָּרוּךְ הוּא אֱמֶת (The seal of the Holy One is truth.)", "source": "Shabbat 55a", "encouragement": "Truth in code."},
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION AND UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def get_config_path() -> Path:
    """Get path to wisdom configuration file."""
    project_root = Path(__file__).resolve().parents[2]
    return project_root / '.exarp_wisdom_config'


def load_config() -> dict[str, Any]:
    """Load wisdom configuration."""
    config = {
        "source": os.environ.get("EXARP_WISDOM_SOURCE", "pistis_sophia"),
        "disabled": os.environ.get("EXARP_DISABLE_WISDOM", "").lower() in ("1", "true", "yes"),
        "show_disable_hint": True,
    }

    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path) as f:
                file_config = json.load(f)
                config.update(file_config)
        except (OSError, json.JSONDecodeError):
            pass

    # Check for disable file
    project_root = Path(__file__).resolve().parents[2]
    if (project_root / '.exarp_no_wisdom').exists():
        config["disabled"] = True

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save wisdom configuration."""
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def list_available_sources() -> list[dict[str, str]]:
    """List all available wisdom sources."""
    sources = [
        # Random - picks from any source
        {"id": "random", "name": "Random (any source)", "icon": "🎲"},

        # Gnostic
        {"id": "pistis_sophia", "name": "Pistis Sophia (Gnostic)", "icon": "📜"},

        # Sefaria API sources (live from Sefaria.org) - HEBREW SUPPORTED
        {"id": "pirkei_avot", "name": "Pirkei Avot via Sefaria.org (Hebrew)", "icon": "🕎", "language": "hebrew"},
        {"id": "proverbs", "name": "Mishlei/Proverbs via Sefaria.org (Hebrew)", "icon": "📜", "language": "hebrew"},
        {"id": "ecclesiastes", "name": "Kohelet/Ecclesiastes via Sefaria.org (Hebrew)", "icon": "🌅", "language": "hebrew"},
        {"id": "psalms", "name": "Tehillim/Psalms via Sefaria.org (Hebrew)", "icon": "🎵", "language": "hebrew"},
    ]

    # Local sources (no API needed)
    for source_id, source_data in WISDOM_SOURCES.items():
        entry = {
            "id": source_id,
            "name": source_data["name"],
            "icon": source_data["icon"],
        }
        # Mark Hebrew sources
        if source_data.get("language") == "hebrew":
            entry["language"] = "hebrew"
        sources.append(entry)

    return sources


def list_hebrew_sources() -> list[dict[str, str]]:
    """List only Hebrew wisdom sources."""
    all_sources = list_available_sources()
    return [s for s in all_sources if s.get("language") == "hebrew"]


def get_aeon_level(health_score: float) -> str:
    """Determine which Aeon level based on health score."""
    if health_score <= 30:
        return "chaos"
    elif health_score <= 50:
        return "lower_aeons"
    elif health_score <= 70:
        return "middle_aeons"
    elif health_score <= 85:
        return "upper_aeons"
    else:
        return "treasury"


def get_random_source(seed_date: bool = True) -> str:
    """
    Get a random wisdom source.

    Args:
        seed_date: If True, same source shown all day

    Returns:
        Source ID string
    """
    # All available sources (local + Sefaria)
    all_sources = list(WISDOM_SOURCES.keys()) + ["pistis_sophia", "pirkei_avot", "proverbs", "ecclesiastes", "psalms"]

    if seed_date:
        today = datetime.now().strftime("%Y%m%d")
        random.seed(int(today) + hash("random_source"))

    return random.choice(all_sources)


def get_wisdom(
    health_score: float,
    source: str = None,
    seed_date: bool = True,
    include_hebrew: bool = None,
    hebrew_only: bool = None,
) -> Optional[dict[str, Any]]:
    """
    Get wisdom quote based on project health.

    Args:
        health_score: Project health score (0-100)
        source: Wisdom source (default: from config), use "random" for random source
        seed_date: If True, same quote shown all day
        include_hebrew: If True, include Hebrew text (bilingual). Default from env.
        hebrew_only: If True, return only Hebrew text. Default from env.

    Returns:
        Dictionary with quote data, or None if disabled.

    Environment Variables:
        EXARP_WISDOM_HEBREW=1 - Enable bilingual Hebrew/English
        EXARP_WISDOM_HEBREW_ONLY=1 - Enable Hebrew-only mode
    """
    config = load_config()

    if config["disabled"]:
        return None

    source = source or config["source"]

    # Check Hebrew settings from environment if not explicitly set
    if include_hebrew is None:
        include_hebrew = os.environ.get("EXARP_WISDOM_HEBREW", "").lower() in ("1", "true", "yes")
    if hebrew_only is None:
        hebrew_only = os.environ.get("EXARP_WISDOM_HEBREW_ONLY", "").lower() in ("1", "true", "yes")

    # Handle random source selection
    if source == "random":
        source = get_random_source(seed_date)

    # Handle Pistis Sophia from separate module
    if source == "pistis_sophia":
        try:
            from .pistis_sophia import get_daily_wisdom
            wisdom = get_daily_wisdom(health_score, seed_date)
            if wisdom:
                # Normalize to common format
                return {
                    "quote": wisdom.get("quote", ""),
                    "source": wisdom.get("chapter", ""),
                    "encouragement": wisdom.get("encouragement", ""),
                    "wisdom_source": "Pistis Sophia (Gnostic)",
                    "wisdom_icon": "📜",
                    "aeon_level": wisdom.get("aeon_level", "Unknown"),
                    "health_score": health_score,
                    "show_disable_hint": config.get("show_disable_hint", True),
                }
            return None
        except ImportError:
            source = "tao"  # Fallback

    # Handle Sefaria sources (all support Hebrew)
    if source in ("pirkei_avot", "proverbs", "ecclesiastes", "psalms"):
        try:
            from .sefaria import get_sefaria_wisdom
            return get_sefaria_wisdom(
                health_score,
                source,
                seed_date,
                include_hebrew=include_hebrew,
                hebrew_only=hebrew_only,
            )
        except ImportError:
            source = "bible"  # Fallback to local bible quotes

    if source not in WISDOM_SOURCES:
        source = "stoic"  # Default fallback

    source_data = WISDOM_SOURCES[source]
    aeon_level = get_aeon_level(health_score)
    quotes = source_data[aeon_level]

    # Use date as seed for consistent daily quote
    if seed_date:
        today = datetime.now().strftime("%Y%m%d")
        random.seed(int(today) + int(health_score) + hash(source))

    quote = random.choice(quotes)
    random.seed()  # Reset

    result = {
        "quote": quote["quote"],
        "source": quote["source"],
        "encouragement": quote["encouragement"],
        "wisdom_source": source_data["name"],
        "wisdom_icon": source_data["icon"],
        "aeon_level": aeon_level.replace("_", " ").title(),
        "health_score": health_score,
        "show_disable_hint": config.get("show_disable_hint", True),
    }

    # Mark Hebrew sources
    if source_data.get("language") == "hebrew":
        result["language"] = "hebrew"
        result["bilingual"] = True  # Local Hebrew sources are bilingual by default

    return result


def format_wisdom_text(wisdom: dict[str, Any]) -> str:
    """Format wisdom as ASCII art for terminal display."""
    if wisdom is None:
        return ""

    icon = wisdom.get("wisdom_icon", "📜")
    source_name = wisdom.get("wisdom_source", "Unknown")

    return f"""
╔══════════════════════════════════════════════════════════════════════╗
║  {icon} DAILY WISDOM - {source_name:<48} ║
║  Project Status: {wisdom['aeon_level']:<50} ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  "{wisdom['quote'][:64]}"
║  {wisdom['quote'][64:128] if len(wisdom['quote']) > 64 else ''}
║  {wisdom['quote'][128:] if len(wisdom['quote']) > 128 else ''}
║                                                                      ║
║  — {wisdom['source']:<60} ║
║                                                                      ║
║  💡 {wisdom['encouragement']:<62} ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Change source: EXARP_WISDOM_SOURCE=bofh|tao|stoic|bible|murphy|...  ║
║  Disable:       EXARP_DISABLE_WISDOM=1 or touch .exarp_no_wisdom     ║
╚══════════════════════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        print("\n📚 Available Wisdom Sources:\n")
        for src in list_available_sources():
            lang_mark = " [עברית]" if src.get("language") == "hebrew" else ""
            print(f"  {src['icon']} {src['id']:<20} - {src['name']}{lang_mark}")
        print("\n🕎 Hebrew Sources:")
        for src in list_hebrew_sources():
            print(f"  {src['icon']} {src['id']:<20} - {src['name']}")
        print("\nUsage: EXARP_WISDOM_SOURCE=<source> python -m ...")
        print("Hebrew: EXARP_WISDOM_HEBREW=1 (bilingual) or EXARP_WISDOM_HEBREW_ONLY=1")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--hebrew":
        print("\n🕎 Hebrew Wisdom Sources (עברית):\n")
        for src in list_hebrew_sources():
            print(f"  {src['icon']} {src['id']:<20} - {src['name']}")
        print("\nUsage:")
        print("  EXARP_WISDOM_SOURCE=rebbe python -m ...        # Hebrew advisor")
        print("  EXARP_WISDOM_HEBREW=1                          # Bilingual mode")
        print("  EXARP_WISDOM_HEBREW_ONLY=1                     # Hebrew only")
        sys.exit(0)

    health = float(sys.argv[1]) if len(sys.argv) > 1 else 75.0
    source = sys.argv[2] if len(sys.argv) > 2 else None

    # Check for Hebrew flags
    include_hebrew = "--hebrew" in sys.argv or "--bilingual" in sys.argv
    hebrew_only = "--hebrew-only" in sys.argv

    wisdom = get_wisdom(health, source, include_hebrew=include_hebrew, hebrew_only=hebrew_only)
    if wisdom:
        print(format_wisdom_text(wisdom))
    else:
        print("Wisdom is disabled.")

