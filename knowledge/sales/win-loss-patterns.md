# Win and Loss Pattern Library

Status: synthetic starter patterns requiring replacement or validation with approved Salesforce history.

## Pattern: Multi-threading improves deal resilience

Signal: only one engaged contact in a multi-stakeholder purchase.
Observed risk: the opportunity stalls when the contact loses priority or influence.
Recommended play: map the buying group and engage an economic buyer, champion, technical evaluator,
procurement contact, and executive sponsor where appropriate. Ask the existing contact for introductions.
Human approval: seller reviews all outreach.

## Pattern: Long time in stage without a dated customer action

Signal: days in stage exceeds the segment baseline and the next step is internal or undated.
Observed risk: close date and probability may be optimistic.
Recommended play: agree a customer-owned next action and date; validate urgency and decision process;
raise forecast risk for manager review. The assistant must not change the forecast automatically.

## Pattern: Tailored validation beats generic demonstrations

Signal: discovery captured concrete workflows and success measures.
Positive pattern: demonstrations mapped to customer priorities produce clearer technical validation.
Recommended play: provide the Solutions Consultant with the top use cases, success criteria, constraints,
and stakeholders before the session. Capture customer feedback after the session.

## Pattern: Late security review creates avoidable delay

Signal: enterprise or regulated customer, sensitive data, integration requirements, or security questionnaire.
Observed risk: security and legal work begins after commercial agreement and delays signature.
Recommended play: identify security owners and required artifacts during discovery or solution validation.

## Pattern: Discounting without value alignment is weak evidence

Signal: discount requested before value, scope, decision process, or competitive position is validated.
Observed risk: lower price does not correct missing sponsorship or weak business justification.
Recommended play: revisit quantified outcomes and stakeholder alignment before requesting an approved concession.

## Pattern: Loss evidence should produce warnings, not deterministic predictions

A similar lost opportunity is a risk indicator, not proof that the current opportunity will be lost. Recommendations
must explain which attributes match, which differ, and what mitigating action the seller can take.





And then we come back with again, the continuation program. Right? I mean, and also some place like I was actually talking to Abhishek also asking him, like, whether we can put all that architectural artifacts in one place so that, you know, uh, even like if somebody want to contribute to that, they can go and contribute or maybe review it or maybe suggest something on it on top of it so that we don't lose what we already gone through. Right? And also people will have a clarity that, okay, we already did this, this, this thing and this, this, this things are pending. And these are our next action item. That is something, uh, I find like a little bit missing in our conversations of this, uh, maybe we can focus on, uh, what we already gone through that maybe recap, week recap three minutes or something like that. And then maybe we can discuss on the topics for today. And then we can take some action items from today, from the discussion.

Notes and action items. Uh, until the prior meeting, I think for the last meeting, I did not. I do have that. I'll publish it. Uh, and to your point, this is what we talked about. I'm just trying to set that, uh, baseline documentation based on our discussion. Uh, I'm those are the kind of draft PR I raised it. Uh, yeah. Today. So maybe we all can put it in here in the same documentation, which will go into the portal that the portal page that you created. Uh, so that it stays in the same place.

Yeah. So it's one thing, um, I'm thinking, uh, Vidhya uh, this one. Right? Especially the new sales intelligence platform that we are planning. Planning to build. So not, not sales because I wanted it to be more like, uh, I mean, there was one conversation. I think you missed it, right? Um, maybe.
You left the call early and then Amrita was pointing, suggesting that we should build something common across customer and sales domain. So it doesn't put that sales word, but instead come up with like context or maybe signal IQ or something like that. Okay, that's one thing. Second thing is, uh, for me, this looks like more than one document, right over there. It is like a collection of documents, like business vision strategy, and then technical yarn, sorry, entity models. And then UI designs. And there are a lot of, I mean, I felt like a playbook in itself would do more justice to the amount of documentation that not just the amount of documentation, amount of the artifacts. I would say. And also one place where we can put all of that, uh, then we can refer to that and add more documents to that. So that's what I'm thinking. More than one document, a playbook in itself would do the, uh.

Justification. That's what I felt like. And I created one. I took the template from enterprise architecture and create a playbook in itself. Uh, for our team, just to keep putting the documents there. And then once it is ready for when, like internally aligned, and this is what our strategy, uh, then we can publish that playbook itself as an initiative playbook.

Okay. So let's focus on this. The remaining two items. Uh, and then we'll come back to this documentation part. So you can. Yeah, sure. You and me can connect offline. Uh, don't want to waste this group's time. Uh, so sheet, I think I'm just going to summarize, uh, where we left. I think in that, uh, entire layer journey, we talked about the first three layers and then the two layers intelligence layer and then the data output layer, uh, we did not cover in our last meeting, uh, will it be a good use of this remaining 23 minutes to focus on those two? Are we there or, uh, how do you, how do you guys want to take it this forward?


Then my suggestion would be, I'll invite.

, a. Anupam in this connect, we have brainstormed specifically on how do we want to build the intelligence layer, right. And intelligence layer is going to be, uh.Uh, anchored into like skill based, um, uh, implementation. Mhm. Has come.Up with an high level idea, which he can give a walk through to this group on what is the thought process behind building and generic intelligence layer, like the way still the architecture is going to be the same. Not.Deviating from what we have discussed in our previous discussions, but the implementation strategy and the orchestration of the intelligence is going to be driven by a skill. And that is what he. I need to work with him to fine tune his thought process further. Simplify it for rest of the group. Also so that it becomes more, um, crisp. Uh, and probably we have this connect coming again on Thursday. So we can get intelligence layer discussion and we can use that Thursday time. I want also like product team to be part of that discussion so that they are aware and in case if they are socializing the capability beyond with the leadership or with stakeholders, they should be aware of, like the intention there to. So let's park that part for Thursday's Thursday, we will be able to give a initial brainstorming of how intelligence is going to be approached within skill based implementation.


Gotcha. And, uh, just upon additional point, from my point of view. Abhishek, I know I've been pushing for this real time thing from like for a long period of time, but the intelligence that you guys are envisioning that would, uh, have a, uh, capability to kind of deploy both, right? The batch base as well as the.

. Smaller model, which are generally less latency and still respond to some of the common or generic queries.
So again, emphasize on two different execution patterns of our layers. One is going to be post call, uh, like an like I when we met last, I summarized it into two different execution pattern. One pattern is going to be more focused on post call and specifically, uh, addressing.
Some of the use cases like signing quality check post call compliance, kind of like implementation, uh, complaints handling, like how GCS wants it. The marketing use case, the Nova three implementation, all of these are post call implementation and, uh, not all of these use cases will follow a real time pattern. So the pattern so far, what our discussion that we did follows that post call implementation. At the same time, we are detailing out, um, basis on outreaches uh, detective compliance use case and what we have learned from, um, objection handling and next best action pattern that will turn into real time use case implementation. And this is identified as a different execution pattern, which would require like a different ecosystem for implementation. The first is going to be more Lumi centric, more, uh, execution in the big data ecosystem is how it will be processed. The other is going to be more event driven. Like at very high level, event driven and Kubernetes.

, uh, so in bits and pieces team is exploring like this area also. And we are crafting requirements so that the POC can be implemented with a business case in mind. So, uh, um.
At high level, I can talk about it, but again, uh, not very concrete, but at least high level is something in case if you want to do a discussion on it, uh, we can do that discussion also. Okay, so this is where I think, um.
Uh, we need to think as a group. Also. Abhishek uh, I mean, definitely we do, we are seeing the requirements from Cedric. Also. They are solving it for real time, right? I mean, um, and second thing is like that, uh.
Documentation, that high level vision and everything like that is still in the deck. Only. Abhishek just want to know. I mean, I started drafting a wiki on top of it. Uh.
So that at least team understand like what we are intending to implement. Um, architecture and the details of it is something that has to be expanded and I can like share it very high level.
Yeah. Because whatever, I mean, the reason I'm saying is like, whatever we are, uh, drafting as something like a sharing with the team, right? Uh, like if you put it in a shareable format, immediately, we will have access to that and go through that later. And do it because whatever that high level vision and the PPT deck, uh, I'm not, it's already shared, right? PPT deck, I think you and Radha has been sharing that, uh, just I wanted rather to also review this requirement once I shared it with Rajiv and Radha to start with. So that at least they validate whether whatever we are building is in line with respect to some of the needs they are seeing, but let me quickly share like, uh, the details that I was mentioning at very high level. Again, it's the same PPT, which I am turning it into more of a detailed documentation. What is the core strategic intent? What's the vision? Uh. That's high level solution overview that we discussed. The other time. The two POCs that we want to implement specifically to, uh, solution patterns. One is real time detection and another is contextual generation, uh, real time signal detection, at least at high level to follow this kind of an semantic wherein we should be able to identify using keywords, using, uh.
distance match algorithms. Plus at the same time, semantic implementation or semantic understanding of the intents also is something that we should be able to detect. I am trying to anchor this whole requirement with respect to our compliance requirement, because the heavy lifting is something that team already did. Identifying those predictors, sharing keywords and intents with the, uh.

Outreach team and seems something that can be mimicked in form of a POC to showcase, like what is art of possible? Uh, this is going to be, uh, like an POC. And in second phase, we can, um, also prioritize the contextual generation implementation, which is going to lean more towards, uh, objection handling and next best action. Kind of like requirement. The way, uh.
AIM team is thinking about it. And both of these two pieces can come together and solve for, uh, real time. Uh, detection and contextual generation in, in, in, in, in, um, in a single, uh, unified layer itself. So I'm trying to like.

Draft like high level requirements, how it needs to be implemented. Mhm. Plus at the same time, I just want to like, uh, let Rajiv and.

Radha's thoughts in case if they are thinking of like anything beyond this that needs to be implemented. Also that can be implemented, uh, included in our first.

POC itself. So that is how we can, uh, quickly get into like this kind of implementation. Further. Yeah, definitely. I think, uh, at least because since we already gone through this high level, uh, requirements and high level thought, like vision process, right? Uh, because even Amruta wanted the teams to even like go and explore the technology, you know, architecture and implementation. So I would like, you know, let Damodar also go back and.Work on this high level and come up with the next level architecture, how it would.
Look like for real time versus post call. And then now we can, uh.
See all of the solutions and then we can, uh, identify which one matches or which one is closer to implementation. That's what I would, uh, recommend.
Like this is something that we can do a.LISTEN — No high-value intervention yet. Separate discussion with Amrut. Given that like an high level architecture is already being prescribed, do we still want to do. And again, uh, a re evaluation of what architecture is not at least I understood is that what we have like a business vision or requirements? This is what we want to do it. But the next level of technical architecture, how we can achieve it, uh, is something.

Uh, you know, we want to, I mean, like, let teams contribute on that and then we can review on it. That's what his point of vision. And I know like how it would go. Let him review and at least I'm ensuring to keep the Damodar posted with all the AI capabilities that we have. I'm already giving him, uh, a dump of like, what's the high level implementation? How?

The overall solution look like? Looking forward to his point of view. Also here. Yeah, definitely. There is anything I think Damotdar, take a look at this, uh, wiki that, uh, uh.

Abhishek has created. And then I think it's not just for you, but for me and who they are. And Hemanth also, uh, also like everybody to go back and see if there is something, uh, we can visualize.
It differently or there is something else we can bring in that will add more value to this overall architecture. Sure, sure, sure. At least what I'm going to do.

At least is like, whatever we have shared with outreach team is something that I'll annotate on top of it to ensure that at least one business specific case is defined and team has a clue of like what needs to be built on top of this. So, that is what I'm, uh, probably by tomorrow I'll get like all those details added. I'm just collecting all the information that we have collected so far. Uh, we'll dump it at one place. Uh, and then, uh, yourself. Damodar can, like, think of how to get it. Crafted as an, uh, as an.
Architectural document. Like the way you were mentioning. Sure. Definitely. I mean, uh, I think we can discuss on that, but I'm thinking that.
Putting everything at one place, uh, so that we can align on that or to. Yeah.Yeah. We can take that off. Right. So. Abhishek um, thanks for actually putting that into, uh, with, um, wiki slash confluence page. So can you just post that in the, in the Slack channel or, or in the chat? Um, I believe you already covered quite a few real time use cases that we have been talking about and captured that, that as well. So that is good. Uh.

Next meeting Thursday. Uh, when the intelligence layer is, uh, walked through, uh, will we, be covering both, uh, the.
Batch based one and real time or how you want to maybe you need a two meetings to cover both like one topic that we have to cover, which is going to be a little deep. And I know it will also lead to like a lot of questions on why it is going to be done and so on. Specifically from post, like the, the architecture and the intelligence layer of it. Right. Um, um, I would say that. Discussion in itself is going to take 30 minutes time because okay, uh, the thought process is something that has to be like, first of all, understood. Um, and how the overall process is going to work is something that we have to do a detailed discussion on. So I would say from my side, we can do that one discussion specifically on the intelligence layer and the design of it and how it is going to be approached as an, um, uh, as a generic use case and how to build, uh, multiple use cases on top of it. So we'll do that discussion in detailed fashion. Yeah.
I think one thing I'm trying to understand is that one is the compliance detection, right? It has its own data, like an on call prompts, right. That has a different set of data and everything, right. And other one is the signals or intelligent signals that can be used, uh, for the sales. Right. That has a different set of data. And, you know, uh, the models probably so how both of them will be supported, uh, together.
Right? Like the way it has to be understood is. Like the layer below layer, specifically the domain, uh, data layer. Uh, then the semantic layer and knowledge fabric layer, the way it is going to be curated, it is going to be agnostic of use case. Here. What can be done is you define as per your domain. So compliance is one domain. Um, say sales assistance is going to be in another one. Uh complaints is going to be altogether a different domain. Marketing can be another domain. All of these domains would have their respective signals. Now what you can do is you can define those raw signals. And that way the layers would be able to extract the semantics out of it. And, uh, store these semantics in a very, um, uh, reusable format. Now on top, you are gonna have intelligence layer with agentic reasoning, uh, context assembly and, uh, um, which we would say that with responsible AI implementation, a generic intelligence workflow would be created. And you can define like different skills, first skill is going to be, say, uh, uh.
Say complaints detection, implementation or complaints detection use case in itself. What it is going to look for is complaints signal in the data and basis on which it is going to add another level of intelligence to do, uh, say hierarchical classification. It is going to be a multi-class classification implementation for signing QC. Uh, similar kind of.
Signals is something that can be leveraged to build summarization on top of it, which is going to be more sales. Uh.

Um, assessment, uh, kind of like summarization. Uh, plus a classification implementation. So probably in next discussion, it would be further clearer that how our use case is going to be be realized. Um, and why the overall construct is going to be like, so, um, uh.
So powerful in terms of scaling, like implementation and building implementations on top of it. So, um, like I would say, let's do. And that's where I'm saying, uh, that discussion in itself is going to take a lot of time because all these questions will be there. Uh, but let's do that discussion on Thursday and, uh, basis on that. We will see like where we are with the overall understanding and, uh, what are the next steps that we have to take? Plus, at the same time, she. She, Anupam, they are take like already, uh, thinking.
Of like the next level artifacts. So to your point, uh, uh, also Srikanth on the documentation side, uh, probably she has a high level, uh, construct which is already there. You may not directly fit into, um, how we want to get it documented. Exactly.
Uh So we have to see like, how can some of the, uh.

Docs basis on which we have white coded the application can be taken forward to draft like ADR and the overall architecture document. So that's been my suggestion would be let's assign someone there who can take the inputs from.

The implementation repository and get it like mapped into, um, high level.
Intentions of architecture or like how we want to express the architecture. Uh, separately because it's going to be in itself, it is going to be very detailed. One. Uh, so, uh, let me add to that. I mean, um, I will check with that. Like how that we can extract the high level documentation from what he has already built. So the reason I put it in, uh, the.

GitHub repo and also the architectural layer of the template is another reason is like, you can use codex or anything, in order to update the documentation. Or maybe use that whatever is already built and, you know, derived from that instead of like spending manually typing everything. Right? So that kind of advantage we get, you know, we can build this out of codex and develop based on that. That's the reason I put it in GitHub. So that we can leverage it directly with all of the tools. And that is what even she has done. Also like it. It is not even like handwritten. These are all generated using Codex only. So you can like briefly connect with.
Them. How can we, you know, put architecture playbook and also have the coding. Uh, sitting close to somewhere like it's like in, in, in a kind of like a monorepo or maybe it has to be separate repo. We will discuss on that. Yeah.

When we talk about this whole architectural documentation, right. Um, I think knowingly or unknowingly, we're just focusing on just the one platform.

And everybody else, you guys will. Will own the entire sales intelligence platform documentation. Uh, I'll leave it to you guys to figure it out, but my goal is to make sure that that documentation is actually part of that overall CRM, as. Intelligence, uh, the AI document, AI governance framework documentation. Because we have the Salesforce component and we have the, our own sales intelligence platform, which we have been talking about. And then we also have a third party AI solutions. For example, we have seismic, we have LinkedIn, we have outreach. So my goal is to make sure that all these things are connected together. And we have a consolidated, uh, you know, the AI architecture and governance framework and also the platform options as well, so that people know which capabilities built, where and which capability should be built, where for any future use cases. So that is my intent. Yeah, I'll leave it to you guys to know. That's a good point. Yeah. That will be the high level documentation that where we'll put in, uh, that is something we discussed about the architecture playbook. I mean, whatever document you put it, I don't want to disturb that. We can keep it alongside. We can derive from this. But what I'm talking about, what's sheath and Abhishek we're talking about is like, it will go a little bit lower because we're talking about diagrams. We are going next level there. Yeah. And so I'll leave it to you guys to decide to the level of documentation that you wanted to put in. But I want to make sure that these are stitched together to our.
Um, architecture playbook or a governance framework so that that information is consumed by the other team scrum, scrum team engineers to make the decisions on the actual solutions. Yeah, that's a very good point. We need to think of like that, uh, decision matrix, like compared to vendor solutions versus custom solution. I mean, this is one area I think we need to constantly keep assessing all the vendor solutions plus our own solution. Yeah.

It could be hybrid solutions as well, right? That some part in like an agent and then some part in.
Our home system. Yep.Yeah. That yeah, definitely. Yeah. Like we will we'll work on it. Uh, internally, like what will be that vendor solution and split on that and then keep documenting that. Yeah. But this group, yes, we need to have that, high level plus that next level documentation, like at one place that we can all refer to that and keep reviewing, updating it. Yeah.
Sure. Okay. Okay. That's good. Uh, anything else? Uh, Abhishek, and you guys want to cover C? I have one.
Thing. We were able to explore. One is going to be like, we can mimic, uh, like from call keeping it into files and then relay it as if it is flowing through a stream. We're talking about audio files or like text files, audio files, text files, text files that can be one way of emulating the calls. Second is at least with Genesis, uh, team were able to hook into some of these live calls and extract Genesis like called transcripts in in real time fashion tool. So that is something that we were like able to explore, but we have to see at what scale and.

Is it also even a compliant way of doing that? Uh, so we have to think of the right way of doing, uh, that hooking into Genesis call. But there is mechanism which can be used with the Genesis APIs itself. So that is something that we were able to explore, but my point here would be like, we will try to emulate the existing calls. Um, and then, um, from files, we'll try to like emulate it as if it is flowing in a stream and then, uh, build like POC on top of it to.

Turn the streaming calls into, um, like a real time. Uh, uh, interaction intelligence implementation on top of it. So if we, I mean, I don't know how to talk to the Genesis team and like other teams within Amex also, like if we get.

to that audio streaming itself, right? I mean, do we have some Amex foundational technology or maybe from EDI to do.

It can be. Collaborate with this team. Yes. Yes, definitely. There will be ideas coming in from this team and they want to do it. Uh, because they are closer to the application right than us. Uh, there's a fact, uh, the thing is, this is.

All new for everyone. That is another fact. Um, I, they are also exploring. We are also exploring and everybody is like theoretical, right? I mean, yes, yes. So he has a, he also had, I mean, when you saw the organisms I just forwarded that announcement to you because we hired you. And also the other.

When you might have been because since you were coming from Wells Fargo and similar ecosystem, I mean, environment, right? Yeah. You eventually see the way it works is, um, there will be some competitiveness. And I would say, yeah, healthy. You have to take it like a healthy competitiveness. And I know, see what you can think of and how we can contribute there. Right? So like.
I mean, that's the reason, uh, when the, the documentation is open and shareable, that's where we can, everybody has the same set of information and then people can go work on their own ideas and come back with a proposal. Yes. So I mean, can I actually share my screen? I was thinking in the similar lines, like, you know, yesterday we were exploring. Uh, Agent creation, right? So I mean, uh, without, uh, I have not set up everything like the back end Postgres or this one. So with that, like I was trying to implement a rack based solution for this. So on the similar line, like if we can implement some agent, which like the hook. Maybe for this, uh, Genesis downstream analysis and all of it, right? Maybe if I can explore that and do a quick post, that would, um, give us like some, uh, you know, maybe can I try? That is what I'm saying. Yeah, I can try that. I can try like, you know, uh, whatever you want to like, uh, so take your. C um, I mean, I, I'm asking, I'm gonna ask, uh, Abhishek gonna share that high level thing, right? Mhm. Yeah. And I think. And then think about next level of architecture. Go to the next step because he talked about different layers. One is the foundation data then is.

The fabric. Another one is the semantic layer. And then on top of it, the intelligence layer. Yes. So that kind of layered architecture he has put in. Yes. So when put your solution or maybe, uh, technical next level design, you have to think of where, where will that fit in? Probably maybe what you are saying, uh, it go into the intelligence layer or maybe it goes into knowledge fabric layer. So that is something you think of.
how skills will be leveraged?where, where will you design a solution will fit in and also not just that one not try to solve one problem, but solve like a, you know, maybe the layer, how are you going to do it? Actually, this is kind of a repetitive, right? We can leverage skills here. Modularly by mapping to the individual agent nodes in the intelligence layer and the other layers also. So my, I mean, uh, during the call, I was thinking in the same, uh, lines because we can leverage the skills as most of is like a repetitive thing. You know, I getting the audio audio from the hooks and analyzing that. Right. Uh, more of maybe I'll just think through, I'll understand more, uh, deeply the problem, like what it is. And then yeah, I can come up with some architecture.
It's more of like, why it's called transcripts, email activity. Yes. Based on that data, we have to do two or like multiple things. Like I think the Cedric, you would have seen that I am ADR, right? The what is Cedric trying to do? I shared that, uh, documentation with you, right? I am. Dogs. Are let me share that folder with you.

So. Uh, I mean, I think because I also ask you something for I am, uh, so. Right. And we need to think of that. Yes. Metrics. Or you.
Okay. Everything is depending on that. And, uh, the outcome is different, right? So sometimes you want to do the compliance monitoring. Sometimes you want to do the post call summary or express actions. Uh, sometimes you want to do the signals thing like, okay, there is a, uh, opportunity for us to, you know, sell or maybe opportunity to send like another card or something. I mean, like basically giving that spend analysis and then, um, looking for, uh. Like recommendations kind of thing, right? What they can do signals. Okay. So, uh, on the, on the same line. Srikanth for this. I am metrics evaluation, right? So is it like the first time we are making this POC or like earlier? Also it was done. How like do I have it? Yeah, with Cedric the first time.

This is the first time. Okay, so so far we have not seen like the because the metrics what she has shown are like very limited. There are many other metrics which we can understand. Definitely. I want you to put in all of those metrics because she's going to sign the contract, right? With Cedric team, but technology wise, we have to ask for all the see, uh, restrictions. Like for me, I would look at, I will tell her that, uh, it has to be approved by our infosec team. Uh, and.

Architecture team and council team, missing team. There are certain groups which has to approve it that I will put as a constraint for them. Okay. That I will take care of it, but I want you to look at from an AI solution standpoint, uh, like think like an you are the gatekeeper or God like, you know, you should, you are, you are buying the software with your own money. Then how do you think what, what are the things that you expect it to have? Right? Yes. And then.

Uh, come up with all of that, even if the list is big, I don't mind. Okay, bring that list. Uh, let you and me review it one time before we share it to Natasha. Okay.


Don't share it. In the meantime, can I, uh, see the product aspects? Like what we are expecting from the product? Uh, so, like, do we have something which is written there? Like I.

Natasha. The same thing because I've been asking her, uh, those, those things, but she did not give it yet. Okay.

There's recount like, uh, getting the.


Thing out of it. Yeah, yeah. Uh, so if I understand the business problem, more of it, right? Like how we are making the complaints, the. Cedric or how it is doing. Right? So something like if we can understand that, like that I can leverage, leverage it in the skills and, uh, whatever we are getting from the knowledge base, which is from the voice transcription, all of it, right? We will convert it into the chunking and embedding and all of that. Like we will do the retrieval. And with the skills and like, we will do the same. Comprehension assessment as a POC. Yeah. So POC is good. Yeah. So, um, can you put it in a, you know, uh, that intelligence layer, right? Uh.

[20:16] Callee
He on.

Thursday. He's gonna demo demonstrate it. Okay. Okay. Uh, like how the intelligence layer would look like, okay, but.
If you have time by Thursday, like, can you visually put in a driver diagram or somewhere on of this overall solution? How it would look like? Yeah.
About the exact condition, because POC will have time. Okay. But the point here, what we are trying to do is we are trying to quickly align on the next level of architecture. So what the, the way architecture works is architecture doesn't have to be proven yet. It's more of like everything is theoretical, right? People will keep based on their knowledge and experience. They go back and draw the diagrams and show something like this would work. This will not work. Uh, they will call out the challenges with the solution. They will discuss the trade offs. Maybe they will say that this will not work for this volume. This will not work for, uh, you know, this is not scalable solution or something like that.

There will be like a feedback or something like that. So one.Uh, understanding what the other people are proposing. And then see whether it is a viable solution or not a viable solution where they could be challenges and then.
You don't have to say it right away, but if you have that doubt in your mind, you go back and assess it. Maybe, uh, improvise that solution, or maybe or what we can do is like. Keep an alternate solution ready. Um, and then at least for Thursday, you don't know anything. I shared that document with you, right? Based on that and based on what your POC you are doing right now. Can you come up with a, a R drive or diagram architecture diagram? How would you how would your solution would look like, like.
Uh, end to. End kind of. Yeah. Sure. Okay. First explain me in the tag here. The problem, the more bottleneck what we see is the ingestion pipeline because the data which we are getting from the downstream, which is like sometimes we may get the late arriving sales transcripts or like, what is it in the real near real time or like how we are getting the transcript streams.

So I'll think I'll, I'll go over the document. What you have shared, and then I'll understand the problem more. So yeah. What, what what today we have is we have transcription Bhumi also. Okay. But those are not like uh, real time. There's a batch runs every hour or six hours kind of thing, like near real time, but not, I would say that, um, not real time also, but it's more of like a batch based transcripts that we are getting it today. That's why, uh, Abhishek is.

Focusing on Thursday on the post call because something that is easy to solve only. So for now, you also think about solving that transcripts are already there with you. How can you solve it for it? Yeah, real time streaming is another problem that we have to solve for that we can take it up, uh, you know, later. Yeah. Like next, like next week or maybe after Thursday. Yes.

Okay. And other things we can work on. Yeah. Because this is something, you know, very important because this will be our future, right? I mean, um, what are the sales intelligence platform that we are building? Uh, I, which will be building and we'll be building.
On like, you know, contributing to that. Um, it's like the way Amrita organization structured, to be honest with you. Damodar is like I asked him the clarity on all of that, right? It will not be see, problem will be there. Problem statement will be there for everybody. Like he want everybody to think on the solutions. Now the senior engineers think about the solutions and let the senior engineers come up with their best solution. And he doesn't want to restrict. Okay, only three constraints should come with the solution. Everybody has to align to that solution. That is not, you know, he is thinking of at the same time, it should not be only Abhishek's team should be coming up with solutions and we have to align with that. That's not the case. Yes. So it's more of a collaborative environment. Um, and also a little bit competitive also. So what I would say is like you always have your own opinion, your own point of view, and then come up with that solution based on that high level, because that high level vision is something we already passed that. I mean, if we had questions on high level, we should have done it like before. But but nobody of us, me or anybody of us did not object to that or did not say anything about it, because it makes sense. I mean, the high level doesn't have much details, right? How it goes. There was no contention also. Yes, it not me. Right. But the next level of designs. There can be contention. There can be alternate solution. There could be different opinions. But we have to have a healthy conversation and align on them. Or maybe, um, you can come up with a new proposals or maybe we can.

Split some work and share and all those things that we can discuss. But if you also think of like your own ideas or something like that, let me know. I will try to get that done.

Okay. Um, yeah. Bye. Most probably by tomorrow. I'll come up with the architectural breakdown of. Based on my thought process and understanding. I'll get it review with you. Yeah.

Yeah. So she said, I'm waiting for the demo link still and we'll share ASAP. Uh.
So that that's something. No. You can now I put it in the loop, right? Yes. After a day or two and just ping Natasha like, you know, when can we expect, uh, a, I mean, she said ASAP, but I don't want to bother her. I'll give her 2 or 3 days and then I'll ask her. Any idea for that? Yeah. Okay. Sure. Um, yeah, this was shared the right. Here in the documents, like overview and everything is there. So that will also help me understand, right. The documents which you shared. I gave some documentations on PPT deck. Was there. Did we share data? Share that or not. Cedric. Uh, document.

One document with Cedric, like, like it's like a executive summary document, which is a.

KPI, OKRs and all. You got it right. She's the document which she's working on. Uh, yeah, that I got it. That I got it from her.

This is about the entire solution. Okay. Yes. I think you if you get the demo that will also help you. But this all should help you to come up with that KPI and expectations for the AI solutions from this one. Okay, okay. Anything else from me? I can tell you, I can help you with that.






