# Zengineering 098 — On Open Source Collaboration

**Recorded:** 2020-08-22 · **Published:** 2020-09-10 · **Runtime:** 01:01:23
**Speakers:** Adam Kerpelman (`adam`) , T. Brian Jones (`tbj`)
**Source:** https://media.transistor.fm/ac89d303/b3682229.mp3

> Machine transcript. ElevenLabs Scribe, word-level timings, diarization on.
> Speaker attribution: `inferred`. Diarized speaker ids were mapped to people by self-identification in the transcript: 'I'm Adam' (21.2s), 'I'm Brian' (22.3s), 'Juris is increasingly' (130.4s), 'I was a manufacturing engineer' (2892.3s), 'people with legal training like me' (3437.1s). Five anchors, no contradictions. The mapping is evidenced; the turn boundaries are still a model's, so confidence stays `inferred` until per-track audio is used.

---

**T. Brian Jones** _[00:00:00]_

Well, you, you... Sorry, go ahead. [chuckles] That's never happened before. In 100 episodes, I don't think we've ever done what we just did.

**Adam Kerpelman** _[00:00:09]_

What? Both tried to yield?

**T. Brian Jones** _[00:00:11]_

Well, yeah.

**Adam Kerpelman** _[00:00:14]_

They don't know what I know. They don't know- Hey, it's Engineering Podcast. I'm Adam

**T. Brian Jones** _[00:00:22]_

I'm Brian.

**Adam Kerpelman** _[00:00:23]_

Welcome back for another hang in the laboratory. It's, uh, just the two of us this week, and we don't need light, we don't need help keeping the lights on. So, uh, let's do it. [laughs] How you doing, man?

**T. Brian Jones** _[00:00:37]_

Get out of here. We don't need your help. Uh, I am, uh-

**Adam Kerpelman** _[00:00:41]_

This is episode 98

**T. Brian Jones** _[00:00:41]_

I'm doing pretty good

**Adam Kerpelman** _[00:00:41]_

... and we don't, we don't know for sure what this project becomes at episode 100, so we're just kinda ticking them off when we have time.

**T. Brian Jones** _[00:00:53]_

Yeah. We're, we're, uh, [clears throat] we're just, uh, we're evolving. We're changing. Things are happening. [laughs]

**Adam Kerpelman** _[00:01:02]_

What, uh-

**T. Brian Jones** _[00:01:02]_

You're, uh, you're about to have a kid.

**Adam Kerpelman** _[00:01:05]_

You're about to have a kid.

**T. Brian Jones** _[00:01:06]_

N- so not as soon as you.

**Adam Kerpelman** _[00:01:08]_

Not as soon as me. Yeah.

**T. Brian Jones** _[00:01:10]_

[laughs]

**Adam Kerpelman** _[00:01:10]_

It's funny to have a... We, we, because of medical circumstances, we have an induction scheduled, so, like, that's weird. I got a hard out [laughs] on this pregnancy.

**T. Brian Jones** _[00:01:22]_

I think that's smart. I know some people who have suggested that we do that because then you're just scheduling things, but they won't let us do that at our hospital.

**Adam Kerpelman** _[00:01:30]_

Yeah, that's fair. Uh, but we're not here to talk about that.

**T. Brian Jones** _[00:01:34]_

No.

**Adam Kerpelman** _[00:01:34]_

Partially, I think because we're both going through that, we'd rather talk about an engineering topic, in a sense. It's sort of engineering. It's like engineering cultural topic.

**T. Brian Jones** _[00:01:43]_

I'd rather nerd rage with you.

**Adam Kerpelman** _[00:01:45]_

Nerd rage. What, uh... Yeah, so what, what's the, what's the topic? Give us our intro, sir.

**T. Brian Jones** _[00:01:53]_

Yeah, I mean, you came all fired up to, uh, to discuss the concepts of open source or open collaboration maybe it'll expand out to, but-

**Adam Kerpelman** _[00:02:04]_

Yeah, I think-

**T. Brian Jones** _[00:02:05]_

... open source software more specifically

**Adam Kerpelman** _[00:02:06]_

... uh, I, I am-- Juris is increasingly, and I am increasingly involved in other projects that are ultimately built on top of open source software. Um, and so, you know, that causes this engineering part of my brain to dig deeper and deeper into the notions of, you know, both technologically what gets us to where we are and how's that novel, and then, uh, culturally-

**T. Brian Jones** _[00:02:34]_

Mm-hmm

**Adam Kerpelman** _[00:02:34]_

... like how does that get us to where we are, right? So, and the realization I have as I cross the sort of... As I try to bridge rivers, I suppose. Um, you know, I talk to a whole bunch of lawyers all the time, and I try to explain to them the way that programmers think about the world in the modern world, and I talk about things like version control, I talk about things like open source software, and they just have no idea what I'm talking about. And then some subset don't even believe that it's possible, even though we have everything in front of us working. And I go, "Yeah, but this is working." And they go, "Mm, I still don't buy it."

**T. Brian Jones** _[00:03:12]_

It's pretty crazy when the legal system is built on open source, right? Open source-

**Adam Kerpelman** _[00:03:19]_

Methodology. Yeah

**T. Brian Jones** _[00:03:19]_

... opinions, open source decisions, open sourced rules and documents, all those, all those funny looking books that are just the same in the background of every legal picture.

**Adam Kerpelman** _[00:03:28]_

Right.

**T. Brian Jones** _[00:03:29]_

That's just open source legal stuff.

**Adam Kerpelman** _[00:03:31]_

So-

**T. Brian Jones** _[00:03:31]_

I guess maybe you pay for them, so the open part's not... But it's kind of open source, right?

**Adam Kerpelman** _[00:03:34]_

Yeah, but it's not supposed to be paid for, and every time somebody challenges that, the Supreme Court goes, "Yeah, you can't, you can't charge for that. It's public." [laughs] Uh, yeah. So let's, so, so, so in this case, when you talk about the laws, like it's easy to, it's easy to see that the laws are meant to be public, right? Um, in this case, maybe the place to start is defining source, 'cause open's easy. We can, we can dig into open and what it means-

**T. Brian Jones** _[00:04:01]_

Is it?

**Adam Kerpelman** _[00:04:01]_

... from a cultural standpoint.

**T. Brian Jones** _[00:04:02]_

Yeah.

**Adam Kerpelman** _[00:04:02]_

But like the first thing that makes the movement that we, that you and I would call open source work is the source code ultimately, right?

**T. Brian Jones** _[00:04:13]_

Yeah.

**Adam Kerpelman** _[00:04:13]_

Source, open source sort of in, at least in the context you and I are talking about, I think, 'cause like obviously source is a broad word. But like from your, from your engineering perspective.

**T. Brian Jones** _[00:04:23]_

Yeah. It's an interesting question 'cause I always, with software I, I... It's easy to kind of spiral down its, into its own little rabbit hole 'cause there's something weird and unique about software and, and that feeling has faded a little bit as I've, as I've progressed in that world in my life, but I'll never forget when I first started really learning to program how strangely unique the whole ecosystem is. Um, but [clears throat] yeah, the source code is, is the program. It's the thing, it-- When you install an app on your, on your, uh, phone, like you're downloading code kind of. I mean, there's a lot of other stuff going on, but, uh, in theory, right? Back in the day when you used to like get a floppy disk, uh, when I was a kid, and people would be like, "Hey, here's a, here's a game," or, "Here's a whatever," uh, you're, you're just getting, you're getting software, and then you, you bring it home and you put it on your computer or you, or you download it into your phone. And then when you like tap it or touch it or I don't even know if people use the word open [chuckles] anymore. Do kids say, "I opened an app"?

**Adam Kerpelman** _[00:05:29]_

When they load it. [laughs]

**T. Brian Jones** _[00:05:30]_

Right when they touch it. Uh, it, the computer runs the code. Like it's, it's just... I mean, it's like a, it's kind of like-

**Adam Kerpelman** _[00:05:39]_

Yeah. So-

**T. Brian Jones** _[00:05:39]_

... a Rube Goldberg machine behind the scenes. The computer's just making the Rube Goldberg machine run.

**Adam Kerpelman** _[00:05:43]_

Yeah. And like I think we got episodes on episodes about this stuff, if we wanna chase it, if you wanna chase through our feed. But like, you know, ultimately a computer is this processing mechanism, and it runs through a string of digits written out that provide it with everything it needs to do all the sort of conditional things that are run in an app, right? But underneath that is just a bunch of code. Like it's a bunch of text. Like you could print out-Like macOS. It would be reams and reams of paper, but you could print it out and go, "Yo, here it is."

**T. Brian Jones** _[00:06:17]_

Yep.

**Adam Kerpelman** _[00:06:18]_

Enter it back in and it'll run. [chuckles] And that's how they used to do programming, on like pieces of paper, right? Uh, a- and-

**T. Brian Jones** _[00:06:26]_

Yeah

**Adam Kerpelman** _[00:06:26]_

... but ultimately, like it, it gets weird because it's just text. And so even from a legal standpoint, like immediately we're getting to the, the legal side, the only way you can protect that is kind of the same ways you protect books and things like that, right? Like you can copyright license your code, and so then people have to pay you to use it. Uh, that's kinda it.

**T. Brian Jones** _[00:06:49]_

Well, it's interesting. Software is interesting technologically too because, uh, it's different, it's different as an entity than like a car, for instance, right? I, and I choose cars 'cause that's maybe one of the more complex things that everybody owns and like deals with on a day-to-day basis. Like if you go under the hood of your car, there's all kinds of stuff going on in there. Seems like a mess, super complicated, and ignore the fact that there are tons of computers and software in cars these days too. Let's just pretend it's all the like moving parts. You got your motors and your pistons and your catalytic converters and stuff. It's pretty complicated in there, but actually if you pull everything out, it's like a known number of parts. You can even pull into those and pull everything out, and you're talking like probably hundreds of thousands of parts, like physical components, and those break down, ultimately down to like a physical thing, like here's a bolt. Software is kind of, it's like infinitely complex, right? Every line of code does something, and each line of code could do that thing like an infinite number of ways. And so when you're dealing with software as a, as like a technological entity, it-- there's, there's this weird thing about it that just makes it like infinitely un- unique, um, and infinitely customizable, and that kind of feeds into, I think, what drives, uh, open source software and why it kind of emerges there. Um, [sighs] do you get what I'm saying?

**Adam Kerpelman** _[00:08:21]_

But it's not-

**T. Brian Jones** _[00:08:21]_

[laughs]

**Adam Kerpelman** _[00:08:22]_

Yeah. I mean, and so this is the thing about having to cover the source piece, 'cause like it's not a new thing to say, "I'm not gonna try to protect." Like this is why I get to the licensing part, right? Like if you invent a car, we live in a governmental system where you get to go, "Okay, I can patent this version of how to put these pieces together," which like nobody's gonna try to do anyway 'cause it has to be done at great cost. But if they wanted to, they're not even allowed to because I have the right to be the only one that does this for a certain amount of time, and has to do with the laws that we've put in place around market economics, et cetera, right? Like, but I think the key part of that is, is, you know, um, [coughs] that I couldn't build a car if I wanted to, right? It doesn't matter if I could get all of Honda's plans-

**T. Brian Jones** _[00:09:07]_

[chuckles]

**Adam Kerpelman** _[00:09:07]_

... for like, you know, a Civic. I can't build a Civic. And so that market is what it is, right?

**T. Brian Jones** _[00:09:15]_

Certainly not easily.

**Adam Kerpelman** _[00:09:15]_

Like Tesla has open sourced all of their patents. It's no help to me unless I'm gonna go start a competing car company, right? So like it's funny that they hold that up as, "Oh, it's been open sourced," and like I'm sure that's got, it's done some good for the world. But like I can't use, I can't go build a car, right? Um, software is just files, digital files on a computer, st- lists of strings of characters that I can, if I have enough disk space, like actually hold and then actually manipulate and then actually, like I can try to build that car because I have everything I need to do it on the device that is the computer. And so the idea of saying, "I'm gonna make everything free," who cares if you do that with a car? It's not a thing that people can really attainably actually leverage as open source. Open source, giving away software is to give away the entire value of that software that you've created. You, you're not-

**T. Brian Jones** _[00:10:15]_

Yeah, well you-

**Adam Kerpelman** _[00:10:15]_

... gonna be able to monetize that through the existing-

**T. Brian Jones** _[00:10:17]_

You're definitely touching on an important-

**Adam Kerpelman** _[00:10:18]_

... I invented it port that people are used to-

**T. Brian Jones** _[00:10:22]_

Yeah

**Adam Kerpelman** _[00:10:22]_

... if you go open source-

**T. Brian Jones** _[00:10:23]_

Totally

**Adam Kerpelman** _[00:10:23]_

... your software, right? And part of that is the code. Like because it's just code written down, we can move it around through the idea system instead of having to move it through the physical world. [chuckles]

**T. Brian Jones** _[00:10:33]_

Well, you're touching on another really critical part of software that makes it a weird n- space. It's entirely virtual. Uh, maybe that's not the right word, but it's, it's, it's fungible, right? You can reproduce it an infinite number of times, and it kind of doesn't cost anything, and everyone can have it. Uh, whereas the car, like in, in service of later parts of this conversation, I think the open source concept with hardware makes sense too, and we're seeing a lot of that also. But it's just so much harder. You have to go buy... The cost of a car is mostly captured in the parts, right? There's, the company's gotta make profit, but you have to go buy an engine and like physically get it to your house, and they're really heavy. And it's still complicated and challenging. There's still all kinds of engineering, uh, necessary to put a car together, uh, just like getting a computer up and running from scratch. But y- it, there's no cost. If you have a computer already, to add software to it, there's, there doesn't need to be a cost. The value of buying software is like entirely artificial, right? And, and I mean that in like an economic sense, right? A, a, a, a car, the company who made the car for you has to, at the very least, like pay for the steel that the car is made out of, right? They can't get around that. They can't give you a car without having paid for that steel. With software, they wrote it, and fine, that costs them money, but now they could just give out the software to everyone, which you can't do that anywhere else. You can't do that in the physical world. And so that's an incredibly distinct component, uh, of open source software. And what's-

**Adam Kerpelman** _[00:12:12]_

This is maybe-

**T. Brian Jones** _[00:12:13]_

... dri- driven it, right, and allowed it

**Adam Kerpelman** _[00:12:15]_

Well, and this is maybe a, a tangent, but like this is also I think is the fundamental thing that people struggle with in cybersecurity conversations. The scariest thing about the idea that the 2020 bar exam might get hacked is everything is digitally replicable one for one at the speed of the internet. So for this two-day, eight-hour-a-day test, if someone finds an exploit on day one, every hacker in the world knows about it and how to do it and has the, has the hardware and the access to execute it for eight hours the next day.

**T. Brian Jones** _[00:12:54]_

Yeah.

**Adam Kerpelman** _[00:12:54]_

Like, and people are like, "Yeah, well." It's like n- it immediately like seems to break the human scale brain-

**T. Brian Jones** _[00:13:01]_

[chuckles] Yeah

**Adam Kerpelman** _[00:13:02]_

... when you, when you, when you take away scarcity. Uh-

**T. Brian Jones** _[00:13:05]_

Yeah, you certainly can't... This stuff, this snowballs so quickly, right? You can't talk about open source software, or you shouldn't, without talking about the internet, right? 'Cause now all of a sudden, to continue the car analogy, if I am tinkering with my car at home, say I've got a machine shop in my garage and I like mill myself a turbocharger and install it on my own car, I can tell people about that, right? I can go tell my friend. I can go help them in their shop build one, and cool, we've both hacked our car. But I can't put it on the internet and have every car in the world all of a sudden have a turbocharger, right? That's what happens with software. It, it, and, and with the internet, right? I can, I can go into a piece of software and I can make a change, and anyone who wants that change now can just come have it. And in the modern world, they can come have it instantaneously, right? There's systems set up to just pr- to instantly make these upgrades as they're contributed to open source projects, which realizing we're way ahead of ourselves on-

**Adam Kerpelman** _[00:14:07]_

Yeah

**T. Brian Jones** _[00:14:08]_

... depth, right? We need to-

**Adam Kerpelman** _[00:14:09]_

No, but I mean that, but it gets to the next-

**T. Brian Jones** _[00:14:11]_

Bring it back in a little bit and explain

**Adam Kerpelman** _[00:14:12]_

... the next point that I wanted to make was like, okay, so, so we're starting from the, the, the fact of code exists and software's weird, blah, blah, blah, right? Uh, the next thing, and this is the part that blows my mind when I talk to like professionals about it, we have to talk about the extent to which without open source thinking, literally none of the stuff that we are d- that we just talked about, all that internet shit, your email, text messages, uh, uh, uh, uh, uh, uh, this conversation we're having right now via video chat doesn't exist without open source projects, and I don't think people understand that, right? Like, I think a lot of people's conception of the internet is like Steve Jobs invented it in 1984, and they're geniuses, and that's why Apple should have so much money, and that's not really the evolution of this stuff. Like, if you wanna get real deep on it, we have episodes about routing protocols and about how the internet works. But like ultimately, what we're talking about is, you know, like the movement that is the meme, the notion of open software, that idea where somebody just went, "Well, let's just give this one away. What if we all agree to not make money off of this? You know, and what we're gonna do is because this is only protected by license, we're gonna come up with a license where no one's allowed to use this who doesn't also agree to allow the next person to use it for free too."

**T. Brian Jones** _[00:15:39]_

It's a funny impulse, right? And I think at the very least it proves that, uh, if you reduce the cost to someone to free, we as humans, uh, are in some capacity altruistic [chuckles] right? It's kind of a proof there. Uh, some people still aren't. Some people still would never wanna give away something they worked hard on, and totally makes sense, right? 'Cause that is the opposite of like how evolution works, right? If you put energy into something, you need to get it back, or else your lineage is gonna die off. So, uh, it's weird, and it kind of exists. My head's deep in politics right now, obviously, as I expect a lot of people are, but it kind of exists in that same philosophical split of like, do we, do we keep things and capitalize on them entirely to like maintain control over things in the case of like Windows-

**Adam Kerpelman** _[00:16:31]_

And to extract all the possible value-

**T. Brian Jones** _[00:16:33]_

Right

**Adam Kerpelman** _[00:16:33]_

... for ourselves, right?

**T. Brian Jones** _[00:16:34]_

Or, or, or is there like a greater good that can be achieved with long-term progress by sharing things out? And honestly, it doesn't... You can argue both, right? Like they're, it's really interesting when you start to look at open source software versus like closed source software. It's owned by companies.

**Adam Kerpelman** _[00:16:52]_

Right.

**T. Brian Jones** _[00:16:52]_

Both are hugely successful, and you see these, this like up and down battle over the last 50 years as, as businesses take these different angles. So it's, uh, it's really interesting to kind of see those different philosophies play out, uh, in the space of our world.

**Adam Kerpelman** _[00:17:08]_

And so, yeah, and so ultimately it's, it's, it, you know, it becomes a public versus private question. You know, so it's not a new challenge, right? You can literally go read the Federalist Papers if you wanna start to break down the idea of what is the public good and how should we leverage it in systems of banking and et cetera, right? Um, and so it, it seems to me that it's just sort of like an ebb and flow conversation, and, and in the space of collaboration, there are times for the open piece and there are time for the closed piece, and they just sort of flow in and out, right? And I think we're living through a change in that mindset right now, which is why it comes up in politics a lot. But ultimately, that change is brought on by the technology we're talking about, right? So the places I like to take it back to with open source is like, never mind sort of the popular examples we'll get to in a second that I think, you know, uh, uh... So when we'll start saying names that people might recognize in terms of brands and things like that [chuckles]. Um, y- you know, it starts at the idea of what gave us the internet, which is protocols, right? So email works because everyone that had servers at the time that the internet was being invented, and that was still enough people that you could go like, "Yo, all you'cause it's just like a bunch of universities, academics at universities. Somebody said, "Hey, if we use this codified instruction set to send messages back and forth," and by codified I mean it's in a code file so it can't work another way, not like put in laws, which is codified. So, like, then we can send email back and forth. And all people have been allowed to monetize ever since then is like, "Hey, here's a novel interface for email." But the reason email works, like no one-- That's not true. A lot of people listening to this have probably heard of SMTP, but the people I wanna talk to have never heard of SMTP, right? It's just the underlying software that makes email work, and email works as widely as it does because that shit's free.

**T. Brian Jones** _[00:19:11]_

Yeah. Another interesting piece with the, with the concept of open source that you see that I think is really, uh, kind of counterintuitive, um, but also like, again, a recognition of these competing philosophies both having value. Uh, s- much, some open source licenses, a lot of open source software is allowed to be shared freely, but also you're allowed to go, like, use it to build a product and build a business around, which is, like, the ultimate perfect combination, right? It's like, "Hey, I've, I've made this thing. It-- For whatever reason, I got the value out of it that I needed. I don't need any more value. Let me pass it along." Uh, and then-

**Adam Kerpelman** _[00:19:58]_

Yeah. Hey, monetize it if you want

**T. Brian Jones** _[00:19:59]_

... not only, yeah, not only can you have it-

**Adam Kerpelman** _[00:19:59]_

If you got a better idea than me, like, monetize it

**T. Brian Jones** _[00:20:01]_

Yeah, totally. Which it's really easy to get caught up in that philosophy and be like, "Well, that's obviously the way forward, right? Like, if I enable you, then you enable other people, and like, look at all the abundance that'll come from that geometric expansion," which, uh, kind of is that, is that philosophy on that side, right?

**Adam Kerpelman** _[00:20:23]_

Yeah. And, and, and, and you know, I'm, I'm an Apple shareholder for a reason. Like, there is an argument for, "Hey, take all that stuff, make it actually usable," [chuckles]

**T. Brian Jones** _[00:20:33]_

Make it-

**Adam Kerpelman** _[00:20:34]_

"Put it in a shiny box," which just costs money, "and then sell it to people."

**T. Brian Jones** _[00:20:38]_

[chuckles]

**Adam Kerpelman** _[00:20:39]_

Um, you know, that, that, that gets to exist. They're not like, uh, they're not, it's not a binary, which is a term I chose carefully. [both laughing] It's not, it's not a binary, you know, sort of operations system, right?

**T. Brian Jones** _[00:20:53]_

You're touching on another really critical piece of this, which is, like, functionality, and this is part of the big argument a lot of the time. Like, Apple argues that they should have-- They've always had this, this, uh, I don't know if it's like rules or terms of service or what, but they very, very strictly control how their software works and how software that you build that runs on their machines work, right? Apple, anyone who builds software apps for the Apple Store versus apps for, like, the Google, uh, Google Store or, or, uh, Android Store, uh, very different process, right? Very strict in how you build Apple. And so Apple software and then Apple from a hardware perspective does the same thing, right? You can't just go buy a bunch of parts to, like, build an Apple computer in the same way that you can with a PC. So the operating system needs very specific stuff, and so what you get is, like, a very pristinely clean, uh, physical hardware system and software that runs on it, right? Like, it just, it's... I know p- I know it's a flame war between Apple and, and Windows, but it's just, it's silly to have it. Apple stuff runs better.

**Adam Kerpelman** _[00:22:01]_

It's a, yeah.

**T. Brian Jones** _[00:22:01]_

You might not like it as much-

**Adam Kerpelman** _[00:22:02]_

It's a bullshit flame war

**T. Brian Jones** _[00:22:03]_

... and it may be different, but, um-

**Adam Kerpelman** _[00:22:04]_

It's a bullshit flame war 'cause the people having it understand why Apple stuff is better. They just can't afford it.

**T. Brian Jones** _[00:22:10]_

Yeah. It's not fair to say-

**Adam Kerpelman** _[00:22:10]_

And it makes them pissy

**T. Brian Jones** _[00:22:12]_

... better either necessarily-

**Adam Kerpelman** _[00:22:13]_

Right? Like-

**T. Brian Jones** _[00:22:13]_

... right? 'Cause they're, the benefit is that you can do whatever the hell you want with those other systems, right? I can build anything and throw it on-

**Adam Kerpelman** _[00:22:19]_

Yeah, right

**T. Brian Jones** _[00:22:19]_

... to an Android phone, whereas there are all kinds of limitations on Apple phones which actually are really bad. They hold back innovation. Um, like for-

**Adam Kerpelman** _[00:22:27]_

Yeah, for sure. I don't, I mean better in the just sort of like-

**T. Brian Jones** _[00:22:30]_

Yeah, totally

**Adam Kerpelman** _[00:22:31]_

... 50 million people can't be wrong way. It's like, look, the Apple is worth what it's worth because that way of doing it works, man. I don't know what to tell you. Uh, at the same time, none of the stuff I spend all day doing works if... Like, I spend all day working with people on running Linux on their laptops. [chuckles] So like-

**T. Brian Jones** _[00:22:50]_

[chuckles]

**Adam Kerpelman** _[00:22:50]_

And then, but that also means I frequently have to troubleshoot shit for them because the software doesn't work perfectly. [scoffs] "I can't screen share."

**T. Brian Jones** _[00:23:00]_

[chuckles]

**Adam Kerpelman** _[00:23:01]_

"Well, are you running Linux?" "Yeah." [sighs] "Okay. Here's the 10 things I need you to do right now, which includes dropping code into the core Linux kernel." Like-

**T. Brian Jones** _[00:23:12]_

Wait, do you run a Linux machine?

**Adam Kerpelman** _[00:23:14]_

No. [chuckles]

**T. Brian Jones** _[00:23:15]_

You just use... You're right. Okay.

**Adam Kerpelman** _[00:23:17]_

No, I don't. I don't. I got nothing to prove.

**T. Brian Jones** _[00:23:20]_

[laughs]

**Adam Kerpelman** _[00:23:21]_

[sighs]

**T. Brian Jones** _[00:23:21]_

It's a struggle if your primary desktop is, like, total open source everything.

**Adam Kerpelman** _[00:23:26]_

No, totally.

**T. Brian Jones** _[00:23:26]_

Good luck. [laughs]

**Adam Kerpelman** _[00:23:28]_

But, so I mean, and this is kind of the relevant transition without... I, I got, if you want me to kill 10 minutes on Riot versus Apple in the context of app stores, I'm, I'm, I'm raging on that, [laughs] that bullshit bad faith representation-

**T. Brian Jones** _[00:23:44]_

No, we, we got it

**Adam Kerpelman** _[00:23:44]_

... from Riot of what the fuck happened. But I don't... Anyway, um-

**T. Brian Jones** _[00:23:48]_

Wait, what's Riot? Oh, is that the, the gaming port?

**Adam Kerpelman** _[00:23:50]_

I think it's Epic. Yeah. Like, they wanna make more money, so they're pulling their shit out of Apple's App Store, and they're p- the Fort- the company that makes Fortnite-

**T. Brian Jones** _[00:23:59]_

I get it

**Adam Kerpelman** _[00:23:59]_

... is throwing their weight around to try to change App Store dynamics.

**T. Brian Jones** _[00:24:02]_

Which is how the world works, right?

**Adam Kerpelman** _[00:24:03]_

Um-

**T. Brian Jones** _[00:24:03]_

You just throw your weight around. [chuckles]

**Adam Kerpelman** _[00:24:05]_

Yeah. They just, they have ret- they have referred to a bunch of things as retaliatory in press releases-

**T. Brian Jones** _[00:24:12]_

Mm

**Adam Kerpelman** _[00:24:12]_

... that really, it, that, that tack strikes me as particularly bad faith. They broke a rule, and then Apple automatically did the thing that the store does when you break that rule.

**T. Brian Jones** _[00:24:22]_

Yeah.

**Adam Kerpelman** _[00:24:23]_

Which is exactly the mechanism that has protected us for a really long time from things like money scams.

**T. Brian Jones** _[00:24:29]_

This is why we need all human emotion removed from every decision that's made.

**Adam Kerpelman** _[00:24:32]_

And then they say it's a retaliation. Well, yeah, like it's a retaliation the way-- Like, the city's not retaliating against you when they give you a parking ticket. You broke the fucking rule. They're cites- giving you a citation for breaking the rule. They're not retaliating against you with an oppressive... What? Representation of the fact that you broke a rule? It was on the fucking sign right there. You don't have a right to not obey that rule because your car is nice. God, Los Angeles has ruined my brain.

**T. Brian Jones** _[00:25:00]_

Oh, Los Angeles.

**Adam Kerpelman** _[00:25:02]_

Uh, [chuckles] anyway. So that's Riot. That's Riot and Apple. That said, I think it's time for Apple to probably rethink its App Store dynamics around some of these things. Like, payments are getting weird again, and we gotta look at that. Um, but like, you know, Apple literally employs people to make sure that your things aren't a scam that's, you know, your apps in the store aren't gonna steal, uh, $10,000 from you and then run away with it, which happens-

**T. Brian Jones** _[00:25:30]_

Good

**Adam Kerpelman** _[00:25:30]_

... constantly with apps on Android.

**T. Brian Jones** _[00:25:33]_

And, uh, that touches another interesting place with software, right? If you, uh, if the software's not protected and taken care of, you can easily get screwed by it, right? It can take over your computer. It can delete your hard drive. It can turn your computer into, uh, part of a botnet, which then is going out and breaking all kinds of laws around the world, doing illegal things, and you don't even know it's happening.

**Adam Kerpelman** _[00:25:56]_

Yeah, which, like kinda kicks back to the security thing, which is like, you know, bad code can be really powerful, and that bad code can be open. [chuckles]

**T. Brian Jones** _[00:26:06]_

[laughs]

**Adam Kerpelman** _[00:26:06]_

So all that is open is not virtuous necessarily, right? Um, and I, I... You know, like everything we've said to this point, I think sort of gets this thing. It's like, okay, so you can tell just by the way that we talk, and I hope that we have otherwise introduced it sufficiently. Like, the idea that there's, there's a cultural split ultimately between the idea of like this stuff sh- is the stuff that should be open, this stuff's the stuff that's not. Everyone is in an ecosystem where we have to acknowledge that open stuff is helpful, 'cause otherwise we don't have email, you don't have text message. Like, communication protocols, we're generally pretty good at being like, "Okay, you can't lock that one down."

**T. Brian Jones** _[00:26:43]_

I don't, we don't think there's-

**Adam Kerpelman** _[00:26:45]_

We need that to work.

**T. Brian Jones** _[00:26:45]_

I don't think there's anything... I mean, there, there's no piece of software that the average person is familiar with that's not, uh, absolutely crippled if all the open source stuff was pulled out, right? I don't think your car-

**Adam Kerpelman** _[00:26:58]_

No, 100%

**T. Brian Jones** _[00:26:58]_

... would run, the internet doesn't work, your computer at home wouldn't work. Every, everything would break instantly.

**Adam Kerpelman** _[00:27:03]_

Google Heartbleed bug.

**T. Brian Jones** _[00:27:03]_

Every-

**Adam Kerpelman** _[00:27:04]_

Yeah

**T. Brian Jones** _[00:27:04]_

... the entire world would stop working if we pulled out open source.

**Adam Kerpelman** _[00:27:06]_

The encryption protocols that run the internet work because they're maintained by a nonprofit who's not allowed to make money-

**T. Brian Jones** _[00:27:13]_

Mm-hmm

**Adam Kerpelman** _[00:27:13]_

... off of that thing.

**T. Brian Jones** _[00:27:15]_

Yep.

**Adam Kerpelman** _[00:27:15]_

Like, literally go Google heartbeat, Heartbleed bug.

**T. Brian Jones** _[00:27:18]_

Yeah, this is not a-

**Adam Kerpelman** _[00:27:19]_

And learn about the 36 hours banks spent thinking they were just c- completely fucked. [laughs]

**T. Brian Jones** _[00:27:25]_

There's no, there's no hyperbole in those comments. I, I-

**Adam Kerpelman** _[00:27:28]_

No

**T. Brian Jones** _[00:27:28]_

... I mean, I'm guessing a little bit that everything, but, um, it, it's... I'm trying to speak to the how much complexity there is in the layering of software in the world, right? To make your computer work, to let you video chat, to let you send a text message, there are just hundreds and hundreds of layers of, of things interrupting, interrupt- interruptable? [chuckles]

**Adam Kerpelman** _[00:27:48]_

Interacting.

**T. Brian Jones** _[00:27:48]_

Interacting with each other.

**Adam Kerpelman** _[00:27:49]_

Yeah.

**T. Brian Jones** _[00:27:49]_

Pieces of software working with each other and relying on each other and doing these little micro things. And I think a lot of people probably picture an application as like, uh, just abstract, right? Most people aren't thinking about software, uh, too frequently and how it works and haven't really worked in it much. So you maybe think of an application as like a book, right? Here's a complete thing that I put together. But really it breaks down more as you break it down into the, into the chapters and the pages and the index and the sentences and the grammar. All of those could be different software projects that layer in to make, make the program work. So each chapter in your book or each sentence in your book could be a different piece of software, and a bunch of those are almost always open source. They're things that you can just go look 'em up. Anyone can use them. They're freely available. Um, because part of what's neat, again, with software where you, where you really quickly hit all these interesting philosophical places is there kind of are, you are able to do things, at least at a very small scale when you're looking at a very tiny, specific, well-defined problem in computer science. You kind of can do them in the best way, and everyone can say, "Okay, that's the optimal program. Let's use that one now." Um, it usually breaks down at a lower level than just the software. Um-

**Adam Kerpelman** _[00:29:06]_

Yeah

**T. Brian Jones** _[00:29:06]_

... but-

**Adam Kerpelman** _[00:29:06]_

I would say it allows for a system where the optimal solution emerges.

**T. Brian Jones** _[00:29:12]_

That's certainly true, too. That's what-

**Adam Kerpelman** _[00:29:13]_

Which is a really crazy way to say it, right?

**T. Brian Jones** _[00:29:15]_

... the open source helps be.

**Adam Kerpelman** _[00:29:15]_

I mean, you can-

**T. Brian Jones** _[00:29:15]_

Yeah

**Adam Kerpelman** _[00:29:16]_

... you can have agreement that this is the right way to solve it, or you can have this way that everybody seems to use and it hasn't broken, and okay, we're all good with it.

**T. Brian Jones** _[00:29:24]_

Well, that's usually actually where it ends up, which is funny to notice, is that it ends up, you recognize that there is the, there is the ability to optimize and come up with the best way to do something. But what you realize is that in the organic world, what really ends up winning is popularity again, even in software. This thing was just adopted. And I don't mean popularity in the sense that like, "Ooh, everyone loves this one the most. He's the coolest. Let's elect him, uh, prom king and queen." But it just is the one that got used the most, uh, incidentally, and now-

**Adam Kerpelman** _[00:29:56]_

Yeah

**T. Brian Jones** _[00:29:56]_

... you have to keep using it because everything runs on it.

**Adam Kerpelman** _[00:29:59]_

And so there's, there's... You know, what's interesting with that, that gets us into the sort of emergence of... Like, the last thing we gotta talk about is Git and version control, and then after we've explained that, I think we can really jump off the cliff of like-

**T. Brian Jones** _[00:30:12]_

[laughs]

**Adam Kerpelman** _[00:30:12]_

... why this creates weird tribes of open source developers who all believe different memes and, eh, believe in different cryptocurrencies. But, like, fundamentally, it's this layered system, and all of those systems are complex, and all of those systems talk to one another, and it's all code, so it's all really rigid. If you're off by a comma, the shit just doesn't work.Right.

**T. Brian Jones** _[00:30:37]_

Mm-hmm.

**Adam Kerpelman** _[00:30:37]_

So that's the nature of all of the interconnected things, right? And some are open, some are closed, and then you have this emergent situation that we've, that we sort of, I think have introduced. On the open side-- On the closed side, there's a limited team maintaining that software, right? Apple's gonna push updates to fix things. Everybody's used to this cycle now in the modern world, right?

**T. Brian Jones** _[00:31:01]_

Mm-hmm.

**Adam Kerpelman** _[00:31:01]_

Like, you get software updates, they're for security, they're for usability, they're for prettier buttons, whatever the, you know, whatever, right? They have a limited team there, I don't know, 1,000 people in Cupertino, that is their dev squad working on X, Y, and Z thing, right? Uh, an open source project with 500,000 contributors has 500,000 programmers always watching that code base and going, "Ooh, I don't like that bug. I'm gonna squash it. Oh, that's dangerous. We should all try to fix that right now full-time until it's fixed."

**T. Brian Jones** _[00:31:34]_

Mm-hmm.

**Adam Kerpelman** _[00:31:35]_

And then eight hours later, the bug is squashed and out of the software [chuckles] like-

**T. Brian Jones** _[00:31:39]_

Yeah, that's, that's the concept for sure.

**Adam Kerpelman** _[00:31:41]_

Um-

**T. Brian Jones** _[00:31:41]_

I mean, it, it probably, if you look at numbers, it kind of scales similarly.

**Adam Kerpelman** _[00:31:45]_

Yeah, no, I mean, right. It's wicked-

**T. Brian Jones** _[00:31:45]_

Which again, is an interesting place where it-

**Adam Kerpelman** _[00:31:48]_

Right

**T. Brian Jones** _[00:31:48]_

... where like these phil- philosophies, uh, parallel each other, right? Um, God, software's such an interesting point to look at philosophy. [chuckles]

**Adam Kerpelman** _[00:31:56]_

Right. Okay, so let's back up though, 'cause all I, I, you know, introducing all that stuff, the last thing to understand is then Git was invented.

**T. Brian Jones** _[00:32:03]_

Yeah.

**Adam Kerpelman** _[00:32:04]_

Uh, version con- So, so you can imagine how this would be a clusterfuck of human coordination, like trying to take on, like... And this is why it ebbs and flows. It was hard to develop software 'cause you have to keep this code base in sync. Like, and so as your team gets bigger, that becomes harder to do because of all of that layers of-

**T. Brian Jones** _[00:32:21]_

Right

**Adam Kerpelman** _[00:32:22]_

... all of those layers of complexity. And eventually you get to a point where it's just like, eh, it's not worth having a dev team of X size 'cause we do more harm than good when we go off and work on different, like, components of this layered up system. Uh...

**T. Brian Jones** _[00:32:38]_

Yeah. Imagine if, if every ti- Imagine, uh, I'm gonna try to give an example of this. Even, and this is not-

**Adam Kerpelman** _[00:32:45]_

Goddammit, Dave missed a comma again. I spent all day-

**T. Brian Jones** _[00:32:48]_

[chuckles] Version-

**Adam Kerpelman** _[00:32:49]_

... trying to figure out why this wouldn't even load. Like, uh, you know? [chuckles]

**T. Brian Jones** _[00:32:52]_

Version control is not a, is not distinct, distinctly needed just for open source. It's needed for any sort of software where there's collaboration, 'cause imagine if when you wrote a book, if like at the end, when you're done writing, like done writing for the day, if you missed that comma somewhere in the book, the book is unreadable, right? The whole book can't be read.

**Adam Kerpelman** _[00:33:14]_

Yeah. [chuckles]

**T. Brian Jones** _[00:33:15]_

It can't sit on your shelf. The shelf catches on fire. Um-

**Adam Kerpelman** _[00:33:17]_

You can't even look at it to find out which-

**T. Brian Jones** _[00:33:19]_

But you can't even-

**Adam Kerpelman** _[00:33:19]_

... which comma you fucked up

**T. Brian Jones** _[00:33:20]_

... you can't even find it. The book disappears from reality until someone like goes into the reality and fixes the comma.

**Adam Kerpelman** _[00:33:24]_

[chuckles]

**T. Brian Jones** _[00:33:25]_

Now imagine you've got 100 people writing the book together, right? And some people are working on the same sentence at the same time. And so I might edit the sentence different than you did, and whether or not the sentence-- Let's say we both made the sentence work right, so the book renders in the world later and people can read it. It still di- we both changed the sentence differently, so how do we like put the book back together? And so that is a really challenging prob- pro- problem, and I think people run into this a lot now actually, 'cause most software is collaborative and most software is run online in, in the cloud, in quote, thrown quotes up. But, um, so you h- you see that on like Google Spreadsheets. If you're both-

**Adam Kerpelman** _[00:34:04]_

Yeah

**T. Brian Jones** _[00:34:04]_

... in there, you can see where the other person is, you can see what they're doing, which like sort of prevents you from editing stuff at the same time, but-

**Adam Kerpelman** _[00:34:11]_

Right

**T. Brian Jones** _[00:34:11]_

... that's even different 'cause with software, I'm editing a different piece of-- Like I'm cloning the car, messing with the engine, and then we're trying to like push those two clones of the car back into one car again. So there's this wild complexity in how that's managed, and, uh, Git, like you mentioned, is, is like the predominant, uh, version control now, and GitHub, which a lot of people have probably heard-

**Adam Kerpelman** _[00:34:33]_

Which is really just like Git, Git is a software codified methodology for maintaining these files.

**T. Brian Jones** _[00:34:39]_

Mm-hmm.

**Adam Kerpelman** _[00:34:40]_

That's it, right? And so you go boop-boop-boop, and you got Git running on your document.

**T. Brian Jones** _[00:34:44]_

Yep. And even, and even with Git, which is again like the most developed, and coincidentally, I think Git was developed by Linus Torvalds, who also invented Linux, so he's like really spiraling into the-

**Adam Kerpelman** _[00:34:56]_

He needed-

**T. Brian Jones** _[00:34:56]_

... the realm of fantasy superhero

**Adam Kerpelman** _[00:34:57]_

... it's the necessary tool to-

**T. Brian Jones** _[00:34:59]_

Right

**Adam Kerpelman** _[00:34:59]_

... create the big open, the most successful open source project.

**T. Brian Jones** _[00:35:01]_

So even, even with that, like the best thing the world has been able to invent for collaborative software development, it's still kind of a nightmare a lot of the time to like keep your software working. It's just frustrating and like you're like, "Oh man, we gotta, you gotta sit down with the other person and work through all this stuff, or the whole team, and like edit things and fight over like, 'Well, should we do it this way? Should we do it that way?'" So there, it's not like you push a button and all of your software works again. I know that's-

**Adam Kerpelman** _[00:35:29]_

Right

**T. Brian Jones** _[00:35:29]_

... kind of the concept everyone wants it to be.

**Adam Kerpelman** _[00:35:31]_

Yeah. But it's, but you n- Part of it is [chuckles]...

**T. Brian Jones** _[00:35:34]_

It is sometimes.

**Adam Kerpelman** _[00:35:34]_

There's a, there's part of being a software developer that I think is hard to appreciate if you're coming from other sectors. There's a time in almost every one of my days where I go, "Okay, I'm gonna press this button, and after I do, my company's website might crash."

**T. Brian Jones** _[00:35:52]_

[chuckles] Right.

**Adam Kerpelman** _[00:35:53]_

And then my boss is gonna call me and go, "What the fuck happened to the website? We're not selling things anymore."

**T. Brian Jones** _[00:35:59]_

Right.

**Adam Kerpelman** _[00:36:00]_

Right? And so we have put in place rollback things where you can-- I've literally had days where that heart-sinking feeling where you're just, you realize you just pushed something bad up to the live thing, and then you go like, I have crashed WordPresses, live WordPress builds for e-commerce stores with significant amounts of traffic.

**T. Brian Jones** _[00:36:18]_

[chuckles] Right.

**Adam Kerpelman** _[00:36:19]_

And I knew how to have that only be down for an hour with backup protocols, but like it's a real thing you deal with if you're a developer in this space, just in a professional context. Like Apple has, Apple uses this shit too.

**T. Brian Jones** _[00:36:30]_

Yeah.

**Adam Kerpelman** _[00:36:31]_

[chuckles] So-

**T. Brian Jones** _[00:36:31]_

Yeah, I mean, so we, we hit on another interesting piece of software, or an interesting aspect of software, and this is not always true, right? 'Cause software runs everything, right? Your car runs on software, planes run on software, spaceships, the electrical grid, everything. But like in the, in the day-to-day w- that I think most people think of software now, like apps on your phone, they're just not very importantIf your app on your, if some silly app on your phone that lets you play Candy Crush or like send a text message doesn't work for the day, really doesn't matter. Um, and so you're able to iterate kind of in the sense of like there's so many bacteria out in the world that it doesn't matter as they like die really quickly and iterate and, and evolve and genetic difference happens. That was a weird analogy to pull out.

**Adam Kerpelman** _[00:37:13]_

It's, it's high volume.

**T. Brian Jones** _[00:37:15]_

[laughs] But anyway.

**Adam Kerpelman** _[00:37:15]_

Like that's what all we have left is biology when we start to talk about internet numbers.

**T. Brian Jones** _[00:37:19]_

Yeah.

**Adam Kerpelman** _[00:37:19]_

There are trillions of apps.

**T. Brian Jones** _[00:37:20]_

You can't, you can't do that with a car. If I, if you open sourced my, my brake system, and then all of a sudden anyone could be editing it and you could push the brake updates to everyone else's cars [laughs] if they were there-

**Adam Kerpelman** _[00:37:32]_

And then your brakes don't work also? Yeah.

**T. Brian Jones** _[00:37:34]_

Right. All the cars blow up. So-

**Adam Kerpelman** _[00:37:36]_

Right. [laughs]

**T. Brian Jones** _[00:37:36]_

... um, there is an interesting, there's... And again, software runs all kinds of important stuff that's outside of the, the world of like willy-nilly, silly Silicon Valley crap.

**Adam Kerpelman** _[00:37:48]_

Yeah.

**T. Brian Jones** _[00:37:48]_

[laughs] Like dating apps and text messaging apps and slight iterations on email. But the, uh, that's an important component of it, right? Is you n- to be able to iterate quickly on this stuff, you have to set up a, a means by which there cannot, there can be critical failure, uh, is kind of removed from the situation.

**Adam Kerpelman** _[00:38:12]_

And so, and so here's my like sort of media theorist take on the fundamental thing that Git achieved, uh, and that we need to roll out in some capacity to every other version of life, uh, where we, you know, in work and whatever. Um, and you s- like you already said, you already cited the places where it's happening, right? Like versions of this way of thinking of a thing are just, it's infectious. And so, and, and it, it also gets us to things like blockchain, uh, which is the way Git, Git tracks literally every single change that happens in the underlying code that is your document. You can use it on a Word doc, you can use it on simpler files, you can use it on wildly complex files, and it just keeps a record of every change that was ever made. And crucially, at least theoretically, a canonical record.

**T. Brian Jones** _[00:39:07]_

Mm-hmm.

**Adam Kerpelman** _[00:39:07]_

So the change and what time, literally of day, but also in what sequence with the other changes every change was made. And when you think of that, it feels like, uh, this kind of gets back to our, our, our like Wolfram episode. Git stopped saying, "Okay, I have a document. You made some changes. Save. Now that's a new document." [laughs]

**T. Brian Jones** _[00:39:30]_

Mm-hmm.

**Adam Kerpelman** _[00:39:31]_

Git said, "I'm just gonna save the extra data. I'm only gonna save what changed and a record of how and when that change was made." And then the file only grows by a tiny bit relative to the size of the other file. [laughs] And so you can have this piggyback on your thing that's just always going, "And then this change happened, and then this person did this thing, and then this person did this thing."

**T. Brian Jones** _[00:39:51]_

Right.

**Adam Kerpelman** _[00:39:51]_

And at any time you can go back and go, "Okay, that changed, and then it crashed. Okay, I'm gonna take out just that change, and everything else should still work. It works. Okay, put it back up." [laughs] Like-

**T. Brian Jones** _[00:40:00]_

And I mean, again-

**Adam Kerpelman** _[00:40:03]_

Uh

**T. Brian Jones** _[00:40:03]_

... that's another place where you start to touch on kind of underlying philosophies of the world, right? The, the universe, as best as we can tell, is keeping track of all the changes, right? When a change is made, it's, it's, it's-

**Adam Kerpelman** _[00:40:16]_

There. [laughs]

**T. Brian Jones** _[00:40:17]_

... a law of, of thermodynamics, right? It, it-

**Adam Kerpelman** _[00:40:20]_

Yeah

**T. Brian Jones** _[00:40:20]_

... if, if you make a change here, it changes something else, and so that, the change that you made here is captured in the change in the other thing. And so that's kind of what you do here because anyone who, especially if you work in like the modern data world as we're seeing the explosion in how important information is, uh, you just, you, y- your urge is to capture everything because even if you don't know how it's useful now, you know it's gonna be useful in a year or a month or a day because the ability to have that information and do things with it is just expanding. And so it's, it's interesting that it's evolved to capture those changes, right? It, it would seem trivial with writing a novel, right? To capture every single time you subtly edited like the, the, uh, language of, of each sentence, right? "Oh, I moved, I, I changed this word to give a subtly different meaning or to describe something in a way that's, that's slightly different." Certainly useful some for the writer as the book's coming together, but ultimately you don't need every single change to be tracked. It's just not relevant. But with software it really can be, right? You have to go back and see how things happen, and you wanna be able to roll back, and you wanna be able to see why, why were these explicit decisions made, which maybe begs the question, is that important for books? Should books be open source and forever changing? Like that's an interesting concept.

**Adam Kerpelman** _[00:41:42]_

Well-

**T. Brian Jones** _[00:41:42]_

[laughs]

**Adam Kerpelman** _[00:41:42]_

... I think the last piece to hit-

**T. Brian Jones** _[00:41:44]_

Spitball

**Adam Kerpelman** _[00:41:44]_

... is one more core thing that's only doable because of software, which is this is kept in a, in a, in what's called an append only sort of, I'm just gonna call it methodology, right? 'Cause the thing is you can make the code work. The idea is the rule of your database is you can't delete an old entry. You can just invalidate it by reference. And so when you have an append-only methodology for record keeping, you-- Like it's, it's, uh, it's, it's more like keeping a, like your checkbook or something, right? Um, if you send out a check, you have to account for that ch- like I don't, I don't wanna t-teach people how to balance their checkbooks.

**T. Brian Jones** _[00:42:26]_

[laughs]

**Adam Kerpelman** _[00:42:27]_

But the point is like you can't just go back and delete an old entry. Instead you have to put up a new change that says, "Now ignore this." Uh, oh, I, I screw up constantly, and I have to roll back and make a change, and the funny thing is I'm just constantly aware that my record of like, "And then he put this up and fucked this up and fucked that up, and then there was another one," like is still there, which is kind of funny.

**T. Brian Jones** _[00:42:49]_

Right. Yep.

**Adam Kerpelman** _[00:42:50]_

But it's there because I know that the underlying infrastructure isn't possible of letting me go back and erase it'Cause that's how the record is kept so that we can achieve the thing that we achieve. And the idea of saying, like, if you try to imagine how to do that, like, with typewriters in a law office, it's like, okay, that-- I mean, you could maybe almost do it there because of how typewriters work. But if you imagine doing that with word processors in an office, it's kinda like, okay, I deleted this line. I, I fixed it. Now the document's updated. Like, why is that a system that doesn't work, right? So, so when you apply it to old models, it, it's weird to think of this idea of like, well, we don't have the... Again, it's a scarcity thing, right? We try to clear out space to put the new stuff in just as, as humans [chuckles] in our brains. But software allows it to just say, no, the rule inside of Git is if you're gonna run Git, the rule is here's how this append-only structure works, right? And so it really does make every single little change trackable. You really can do the thing that you're talking about because of that fundamental thing at the core of how this, like, methodology works, right? [lip smack] Um, when you stack all of that up, y- you, you can work on these massively complex projects together w- with the right coordination, which a lot of times people will at this point have heard of GitHub, if only because Microsoft bought them for a shit ton of money. Uh, GitHub is essentially just a social platform on top of Git. So a way of talking about all the work that you did that was tracked by these things and st- and maintained interoperability because of the work that you did, and created a social layer, essentially, of people that are like, "Yo, let's all work on this project together."

**T. Brian Jones** _[00:44:40]_

Mm-hmm.

**Adam Kerpelman** _[00:44:41]_

With Linux, that was, you know, Git was developed because they were tired of doing that via email, and then GitHub popped up because people were tired of however they were coordinating this thing whilst not breaking the software amongst a bunch of people that just cared to work on the project. Like, just open source gets social really quickly, and so there's this weird social aspect of what we end up talking about with communities and, and, uh, like that piece of it. Um, but I think that's everything sort of technical, right? I mean, fundamentally, the place we're at now is we can make software, we can collaborate on it without breaking the software. A- a- a- and, and, and you start looking at other places to apply it. Like, it just, you just get to weird things I find myself explaining to lawyers all the time, which is like, "This thing, this thing we just templated, no one should ever have to do that again."

**T. Brian Jones** _[00:45:33]_

[laughs] Yeah, that is-

**Adam Kerpelman** _[00:45:34]_

There's no fucking reason.

**T. Brian Jones** _[00:45:35]_

That is a funny concept, 'cause you're right.

**Adam Kerpelman** _[00:45:37]_

And they go, "What? No."

**T. Brian Jones** _[00:45:38]_

We've re- we've reached a point where, uh, for the most part, almost ev- it feels like almost everything has an open source counterpart, right? Like, think of a popular piece of software, uh, and there's an open source version, right? Like Photoshop, yep, open source version. Microsoft Office, all of them have open source versions. Not only do you have, like, the free versions that, like, Google makes available to you, but you can just go get multiple different versions that have large communities that, like, rebuilt Microsoft Word. Uh, it's a little different. It does things differently, sometimes doesn't interop. [chuckles] There, I'm trying to use interoperability again. Sometimes it doesn't work with the other, other tools. Um, it works fine within its own environment. And so as a developer, like, as you're building things... This is funny. I'm making a really interesting connection to my previous engineering work before software. But as you're building software, you, you, you're using other software to build your software, right? You're building on top of it. And so whenever you need a piece of software to do anything, you go search for it first. Like, did someone build this already? Did someone solve this problem? It, the concepts that you, like, learn academically, and I'm not a computer scientist, so I'll often misspeak about this stuff. But I think the concepts, um, [lip smack] are, uh, are called design patterns, and that's kinda what you learn academically, these, like, reduced concepts that you see over and over and over again in engineering and in software. And so, like, you'll see this, you'll see this thing which is like, they'll, they'll be very low level, like how do you solve this logic problem? You'll see them over and over and over again in your software, and they'll manifest in different ways. But when, when you see this, be aware of it and know that the complexity of it has been reduced and solved in this way, and you should always kinda do it this way unless you have a really good reason not to. Um, kinda like how grammar works in, in written, written and spoken language. And so you learn that, but we've reached like a meta level where so much of the next layer of complexity, like how does this software work in this language, on this operating system, with this hardware, in this use case? You just go get it. Someone's built it, and 100 people have helped maintain it. And so we're, we're in a interesting place where so much stuff can be pieced together, and software's too complicated still to, for that to just be like plug and play. Anyone can just, like, touch things together and have them work. But [lip smack] and, uh, you know, it, it touches on th- that realization that I called out there a second ago that was so interesting compared to my old job where I worked in physical manufacturing. I was a manufacturing engineer. I constantly was frustrated by having to reinvent things that I knew had been solved hundreds or thousands of times all around the world, right? In a manufacturing plant where I was building automation, I was building robotics and automating manufacturing processes, I constantly had to solve something. I was like, "This is so simple and silly, but it's not, like, a thing I can go buy." It's, like, ever so complex that whoever has solved this a thousand times before in a thousand different manufacturing plants, they didn't have, like, a means to share it.

**Adam Kerpelman** _[00:48:47]_

You should be the one doing it.

**T. Brian Jones** _[00:48:47]_

I shouldn't have to do this again. And that-

**Adam Kerpelman** _[00:48:49]_

Yeah, you just pitched your first startup.

**T. Brian Jones** _[00:48:51]_

Exactly. That's what drove, that's what drove me to my first startup. And, and I didn't realize what it was at the time. I wasn't actually trying to solve that problem. Um, I was solving something different, related, but... And soThe concept of open source being released into the world more broadly than software is really challenging because it seems to, it works best and maybe arguably only works when things are digitized, which is not true of, like, physical things like car parts, um, although the designs are all digitized now. But it just, it enables such an incredible layering of, like, success and invention and creativity, and it also makes it so apparent how important other people's contributions to things are, right? It makes it s- there's, there's nothing that any modern s- programmer does for the most part that would be even, even, like, imaginable without the incredible underpinnings of everything that, that allow it to happen. Like, modern technology, especially in software and hardware and computers, is so complicated that no one really knows how it all works anymore. And, and I don't mean at, like, a high level I can tell you how a computer works, but I could not even come freaking close to being functional with, like, 99.99% of what's out there. Even in a lifetime-

**Adam Kerpelman** _[00:50:15]_

That's fine

**T. Brian Jones** _[00:50:15]_

... it's just too complicated now, right?

**Adam Kerpelman** _[00:50:17]_

Well, you don't-

**T. Brian Jones** _[00:50:17]_

And it doesn't-

**Adam Kerpelman** _[00:50:17]_

It doesn't matter

**T. Brian Jones** _[00:50:18]_

Well, that's exactly the thing.

**Adam Kerpelman** _[00:50:19]_

You don't speak certain languages.

**T. Brian Jones** _[00:50:20]_

I don't need to.

**Adam Kerpelman** _[00:50:20]_

So you can get an interpreter. [laughs]

**T. Brian Jones** _[00:50:22]_

We talk about this sometimes. I wonder, I wonder how this felt h- even, uh, even just a few hundred years ago when you have, like, the concept of, of, like, a jack of all trades or what's the fancier word for that type of person?

**Adam Kerpelman** _[00:50:35]_

Generalist?

**T. Brian Jones** _[00:50:36]_

Generalist, yeah, where you like-

**Adam Kerpelman** _[00:50:38]_

[laughs]

**T. Brian Jones** _[00:50:38]_

I feel like you-

**Adam Kerpelman** _[00:50:39]_

That's what I call myself

**T. Brian Jones** _[00:50:39]_

... you almost kind of could know everything in a lifetime a few hundred years ago. If you were s- extraordinarily well-read, you could be up to date on, like, everything that's really known in modern science and modern medicine and chemistry. There just wasn't as much happening. And I, I know there's subtlety in, like, the human experience that can't be known and, and emotion and, and how you perceive the world, but in terms of kinda like raw scientific knowledge, you could know such a larger percentage of it, uh-

**Adam Kerpelman** _[00:51:05]_

Right

**T. Brian Jones** _[00:51:05]_

... in times of past, right? And now it's absolutely impossible, right? Even pick the, pick the most specific niche and you can't know it all anymore. Um, so we've reached a point where we have to open source stuff. We have to open source information, and we have to exist in a world where you can trust what's been open sourced, because if you can't, then you can't make progress anymore. We can't go-

**Adam Kerpelman** _[00:51:30]_

Even-

**T. Brian Jones** _[00:51:30]_

... forward if you can't trust the layer that's beneath you.

**Adam Kerpelman** _[00:51:32]_

Even if you hear that and, and, like, have a violent reaction to it, it doesn't matter. It's happening, right? Like, this is also just a force that is not even guided. It's, it's, technology is a force unto itself that's doing what it wants-

**T. Brian Jones** _[00:51:46]_

Yeah

**Adam Kerpelman** _[00:51:46]_

... with us whether we like it or not.

**T. Brian Jones** _[00:51:48]_

I mean, I-

**Adam Kerpelman** _[00:51:49]_

[laughs] Like-

**T. Brian Jones** _[00:51:52]_

It's a weirder-

**Adam Kerpelman** _[00:51:52]_

Wikipedia exists, right? You, like-

**T. Brian Jones** _[00:51:54]_

Yeah

**Adam Kerpelman** _[00:51:54]_

... you might say, "No, we need to keep that locked in an encyclopedia." Sorry, the Wikipedia box is unlocked and it runs. Like, it slaps. [laughs]

**T. Brian Jones** _[00:52:04]_

Yeah. And, and-

**Adam Kerpelman** _[00:52:05]_

And so-

**T. Brian Jones** _[00:52:05]_

... and people are doing everything. There's so many projects to maintain that, right? There are people printing it out regularly and stashing it in vaults so we never lose it. There are people putting it on, on media that will last for m- millions of years and hiding it and preserving it and constantly updating it as it's updated. Like, this, this stuff has meaning and, and we-

**Adam Kerpelman** _[00:52:25]_

Writing it on gold records and firing it billions of miles from the Earth. [laughs]

**T. Brian Jones** _[00:52:30]_

We should definitely launch Wikipedia out on some satellites.

**Adam Kerpelman** _[00:52:33]_

For sure.

**T. Brian Jones** _[00:52:34]_

[laughs]

**Adam Kerpelman** _[00:52:34]_

Uh, but yeah, like, so there's, there's two things to wrap up. If you're also one of those people that listens and hears about cryptocurrencies and DeFi and blockchain and that part of what we talk about, the application of this way of thinking about the world to finance is why that has captured some subset of every young person's mind that I have talked to. They understand what you can do with this-

**T. Brian Jones** _[00:53:04]_

Mm-hmm

**Adam Kerpelman** _[00:53:04]_

... and they're taking down the banks. They're just tired of it.

**T. Brian Jones** _[00:53:08]_

Yeah.

**Adam Kerpelman** _[00:53:08]_

[laughs] They're tired of being oppressed by our financial system. And so, hey, like, w- uh, what will happen? I don't know. But this tiny subset has the tool we just described, and they're using it for money. To not watch that is just ignorant. Like [laughs] I don't know how, I don't know how else to say it.

**T. Brian Jones** _[00:53:26]_

Let me spin it the other way, too. Uh, it, we're just, we just see the opportunity and we're tired of not executing on it, right? The, the-

**Adam Kerpelman** _[00:53:36]_

Right

**T. Brian Jones** _[00:53:36]_

... the systems that came before when they were new were fucking fantastic, and those people were just as thrilled as we are to innovate. But there's so many places we can innovate, and innovation happens so much easier now when it's allowed to that it's even more frustrating when you see the opportunity and it's not being executed on. So comparatively now to 50 or 100 or a couple hundred years ago when a lot of things that exist now that people are so fed up with were being established, we can fix them at a faster rate. We can iterate and improve at a faster rate. We can do it more successfully. We can do it more collaboratively. We can do it more science and technology and statistically based. And so it's just, like, ever increasingly obvious to us that we're wasting time, we're wasting energy when you have to exist inside these systems that aren't operating at efficiencies that we know are just around the corner. We're pissed off. And especially when that expands out into beyond, like, simple things like I, I don't wanna pay a fee when I overdraw my checking account. Fine, I get that you extract money there. That helps run the business, but that's fucking stupid. Don't do that anymore.

**Adam Kerpelman** _[00:54:45]_

Also once every three years-

**T. Brian Jones** _[00:54:46]_

It doesn't need to happen

**Adam Kerpelman** _[00:54:46]_

... the fucking bank loses a lawsuit about fraudulently charging those, and they have to return a bunch of money to us.

**T. Brian Jones** _[00:54:52]_

Right. So let's, let's just-

**Adam Kerpelman** _[00:54:54]_

Why the fuck do you even trust that system?

**T. Brian Jones** _[00:54:57]_

Right. Let's just fix it. Let's fix it.

**Adam Kerpelman** _[00:54:58]_

Anyway, so-

**T. Brian Jones** _[00:55:00]_

We're off, we're, we're out of control.

**Adam Kerpelman** _[00:55:01]_

Yeah, right. Anyways, so that's financial, right? But the l- the other piece, and, and this is backing up to the idea of the generalist, right? Which is, you know, I, I think-Like you were saying, jack of all trades, right? You could know how to do a bunch of things around a town at some point. My life as a producer, then as a project manager, and everything I've ever done has been like, like people say, "What does a producer do on a movie?" Uh, a producer knows who to talk to and in what order, and that's it. And then they help you with creative things, right? Um, and there are people that are better at the creative piece, and they make f- more fun things. But like fundamentally, you can maintain a job as a producer around Hollywood if you know who to talk to and in what order.

**T. Brian Jones** _[00:55:42]_

[chuckles]

**Adam Kerpelman** _[00:55:43]_

Right? And, and, uh, if that's not, like... If that's not a perfect articulation for where this starts to consume knowledge work, is like just knowing that I should talk to a lawyer is the first step, right? When, if you're talking about consuming the law. Um, so already that's gated by the same mechanism that's like, "Well, who do you know?" Well, now I can Google.

**T. Brian Jones** _[00:56:11]_

Yeah. I mean-

**Adam Kerpelman** _[00:56:11]_

So that's already started to fuck with your universe, right?

**T. Brian Jones** _[00:56:13]_

That same, that same workflow applies to absolutely everything, right? As soon as it's, it's a project, it's what do I need to know and in what order? And it's whether-

**Adam Kerpelman** _[00:56:19]_

Right

**T. Brian Jones** _[00:56:20]_

... whether you go talk to someone or you, or now. It used to be you had to go talk to somebody, right? Even, even relatively recently. Like as a kid, I would have to call the library to-- I would ask my mom about something that you would, I trivially look up a thousand times a day now. And we would call the library, and someone would go look it up in a book. Which is-

**Adam Kerpelman** _[00:56:38]_

And if you couldn't find it in that one, you had to go to the other one downtown 'cause it was for-

**T. Brian Jones** _[00:56:41]_

'Cause you called a bigger library

**Adam Kerpelman** _[00:56:43]_

... 'cause it was for a paper, yeah. [laughs]

**T. Brian Jones** _[00:56:44]_

Which is utter insanity in today's world. [laughs]

**Adam Kerpelman** _[00:56:48]_

But so anyway, the thing is like, uh, it, it, the place where it hits cryptocurrency and all the weird stuff that's happening right now, and the reason, like it's, it's all because of all the stuff we just ran through. Which I hope the, at least the way that we presented it-

**T. Brian Jones** _[00:57:01]_

[laughs]

**Adam Kerpelman** _[00:57:01]_

... is like, okay, this is what's happening, and it's, it's consuming parts of the world.

**T. Brian Jones** _[00:57:06]_

It was an adventure.

**Adam Kerpelman** _[00:57:07]_

Like, uh-

**T. Brian Jones** _[00:57:08]_

For sure

**Adam Kerpelman** _[00:57:08]_

... uh, it's coming for knowledge work, like sometime soon. And it's not because AI is gonna think like a lawyer. It's because people with legal training like me can identify everything a lawyer does that no one should ever have to do again.

**T. Brian Jones** _[00:57:24]_

Yeah.

**Adam Kerpelman** _[00:57:25]_

Because software exists.

**T. Brian Jones** _[00:57:26]_

Right.

**Adam Kerpelman** _[00:57:28]_

So, uh-

**T. Brian Jones** _[00:57:28]_

Which has other, all kinds of other implications. If you're listening-

**Adam Kerpelman** _[00:57:31]_

Right

**T. Brian Jones** _[00:57:31]_

... and thinking that's scary and awful, totally agree. [laughs]

**Adam Kerpelman** _[00:57:34]_

[laughs]

**T. Brian Jones** _[00:57:34]_

Right? There's all kinds of scary things to figure out there too, right? But, uh-

**Adam Kerpelman** _[00:57:38]_

It's still gonna take people to tend it, so it's like c- that, that's, that's where we've ended up with Juris. Go learn how to tend it. That's, that's your legal engineering certification, right? Totally different subset. People will have jobs. We're probably fine. There'll probably be two for every lawyer that used to exist. Um-

**T. Brian Jones** _[00:57:53]_

You know, it's easy to be excited about this stuff when you're involved in making it. [laughs]

**Adam Kerpelman** _[00:57:57]_

That's true. Uh-

**T. Brian Jones** _[00:57:57]_

And probably horrifying if you're not.

**Adam Kerpelman** _[00:57:59]_

So that's-

**T. Brian Jones** _[00:58:00]_

Right?

**Adam Kerpelman** _[00:58:00]_

No, it's-

**T. Brian Jones** _[00:58:00]_

So-

**Adam Kerpelman** _[00:58:01]_

I mean, it's also, it's also horrifying to be in it 'cause does it work or not, right?

**T. Brian Jones** _[00:58:04]_

It's also horrifying.

**Adam Kerpelman** _[00:58:04]_

And does it work or not boils down to this funny thing with open source, which is you have to-- it, everything is a test of this is one that should be open and this is one that shouldn't. And, you know, different things win different pieces of the pie there, right? Like-

**T. Brian Jones** _[00:58:18]_

Yeah

**Adam Kerpelman** _[00:58:18]_

... cryptocurrency is a place where the government might be like, "Too many people get hurt if we don't do this through the existing infrastructure. I'm sorry, y'all."

**T. Brian Jones** _[00:58:25]_

Mm-hmm.

**Adam Kerpelman** _[00:58:26]_

And they'll shut it down.

**T. Brian Jones** _[00:58:28]_

That happens all the time.

**Adam Kerpelman** _[00:58:29]_

Uh, to some degree.

**T. Brian Jones** _[00:58:30]_

And sometimes that's right.

**Adam Kerpelman** _[00:58:32]_

Yeah.

**T. Brian Jones** _[00:58:32]_

And often it's, it's not. [chuckles] Often it's the wrong decision.

**Adam Kerpelman** _[00:58:37]_

Um-

**T. Brian Jones** _[00:58:37]_

Oh, I used, I used a word that's not a real word.

**Adam Kerpelman** _[00:58:41]_

Wrong.

**T. Brian Jones** _[00:58:42]_

Yep. There's one thing I've learned from doing this podcast. It's anytime I use a word like wrong or better, uh, any sort of judgmental word, I'm, I'm making something up. [laughs] It's not a real thing, and-

**Adam Kerpelman** _[00:58:56]_

Yeah. The thing-

**T. Brian Jones** _[00:58:56]_

... it, it has no real bearing on the world. It's just me.

**Adam Kerpelman** _[00:58:59]_

Been reading the-

**T. Brian Jones** _[00:59:00]_

Just my own bullshit

**Adam Kerpelman** _[00:59:00]_

... Federalist Papers.

**T. Brian Jones** _[00:59:02]_

[laughs]

**Adam Kerpelman** _[00:59:02]_

And it's interesting, like y- they, they're, you know, more tactful statesmen and better writers than I will ever be. Uh, they still occasionally go to that place, right? Like-

**T. Brian Jones** _[00:59:15]_

It's hard not to

**Adam Kerpelman** _[00:59:16]_

... you're having this, I think, very politically correct thing of like, let's try to pull out from an impassioned perspective. Eh, Hamilton does an awful lot of, "I understand this is an impassioned perspective-

**T. Brian Jones** _[00:59:29]_

[laughs]

**Adam Kerpelman** _[00:59:29]_

... but if we cannot keep in our minds the notion of a public good, we're fucked 'cause Spain is gonna come attack us and take us over." And he means it literally. [laughs]

**T. Brian Jones** _[00:59:40]_

Yeah.

**Adam Kerpelman** _[00:59:40]_

Like-

**T. Brian Jones** _[00:59:41]_

Yeah.

**Adam Kerpelman** _[00:59:41]_

And it's so, you know, there's a time to express that a thing is wrong. I don't know what to, I don't know what to say otherwise, right? Um, I don't think we do too-- I, uh, uh, that's not true. We do a shitload of this on this podcast, but whatever.

**T. Brian Jones** _[00:59:54]_

Oh, yeah. There's a lot of personality that comes out.

**Adam Kerpelman** _[00:59:57]_

Sorry about that shit. [laughs]

**T. Brian Jones** _[01:00:00]_

Quite a bit.

**Adam Kerpelman** _[01:00:00]_

Anyway, thanks for hanging out for episode 98.

**T. Brian Jones** _[01:00:03]_

98. Whew.

**Adam Kerpelman** _[01:00:04]_

On open source and something and-

**T. Brian Jones** _[01:00:07]_

It was a good adventure

**Adam Kerpelman** _[01:00:08]_

... why robots will replace you. I don't, I, I, you know.

**T. Brian Jones** _[01:00:11]_

No.

**Adam Kerpelman** _[01:00:11]_

I don't know.

**T. Brian Jones** _[01:00:13]_

We're a long ways from robots replacing anything. We're not even gonna bother.

**Adam Kerpelman** _[01:00:16]_

Why robots will replace your children?

**T. Brian Jones** _[01:00:18]_

That one's so obvious we're not even gonna bother with robots anymore. We're just gonna have glasses on soon, and then we'll be in that episode of "Star Trek" where Riker brings that weird game back from that, like-

**Adam Kerpelman** _[01:00:26]_

Oh, yeah

**T. Brian Jones** _[01:00:26]_

... fantasy party planet.

**Adam Kerpelman** _[01:00:27]_

That's fucking TikTok, man.

**T. Brian Jones** _[01:00:29]_

Yep. Totally.

**Adam Kerpelman** _[01:00:29]_

Where he ate the little swallows, the little discs-

**T. Brian Jones** _[01:00:31]_

Yep, the little disc swallow

**Adam Kerpelman** _[01:00:31]_

... in like bad povray-

**T. Brian Jones** _[01:00:33]_

Yep

**Adam Kerpelman** _[01:00:33]_

... 3D animation.

**T. Brian Jones** _[01:00:35]_

Yep. Who saves the day? Does Wesley save the day on that one? I think so.

**Adam Kerpelman** _[01:00:38]_

I don't, I don't remember.

**T. Brian Jones** _[01:00:38]_

Even Data I think got sucked into it.

**Adam Kerpelman** _[01:00:40]_

Yeah.

**T. Brian Jones** _[01:00:40]_

Which was like kind of a cop-out, but maybe not.

**Adam Kerpelman** _[01:00:43]_

I thought Data was just busy with something else. [laughs]

**T. Brian Jones** _[01:00:46]_

[laughs] Maybe he was away. He was on an away mission. [laughs]

**Adam Kerpelman** _[01:00:50]_

[laughs] Fixed. Rhetorical device.

**T. Brian Jones** _[01:00:53]_

Oh, boy.

**Adam Kerpelman** _[01:00:53]_

Anyway, I'm Adam.

**T. Brian Jones** _[01:00:55]_

I'm Brian. Keep an open mind, everybody, and share, and share stuff. Actually, let me rewind. Just share some things. Go share something with somebody.

**Adam Kerpelman** _[01:01:02]_

[upbeat music] They don't know what I know. They don't know like I know. All the time. They can't arrive. All the time
