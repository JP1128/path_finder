# PATH FINDER for UGA 
<p>
  <a href="https://devpost.com/software/path-finder-l1zg0x">
    <img src="https://img.shields.io/badge/devpost-PATH%20FINDER-003E54?style=for-the-badge&logo=devpost"/>
  </a>
  <a><img src="https://img.shields.io/badge/Winner-Best%20Overall-F3BF1E?style=for-the-badge"/></a>
  <a><img src="https://img.shields.io/badge/Winner-Most%20Creative%20Use%20of%20Twilio-F3BF1E?style=for-the-badge"/></a>
</p>

Authors: **Jae Park (JP)**, **Jae Oh**, **Geonho Kim**

PATH FINDER is a simple and powerful SMS service that will save you headaches from the UGA bus transit. When you tell us your current location and where you want to go, we will find you the quickest way to get there. It’s that simple. What’s more, you don’t need the internet to use our service!

## Inspiration
If you're riding the UGA bus for the first time, you've probably felt a bit lost. We FEEL you. You’re not quite sure how to use the UGA app, and sometimes you’re scratching your head trying to discover the most optimal path to your next class. Don’t EVEN talk about the weak internet connection in front of Tate. Feeling frustrated yet? That’s why we created this project.

## How We Built It
We used Python with Flask, UGA transit, Google Maps Platform, and Twilio API to bring this service to you. It’s already up and running 24/7 on DigitalOcean’s virtual cloud machine.

## Challenges We Ran Into 
It was difficult to test drive our service due to only 2 buses running on the weekends :’(. But, we were extra careful to make sure our implementation can be generalized to when there are more buses!

Also, we couldn’t find any documentation on the UGA transit API, so we had to do some research with our trusty friend F12.

## Accomplishments That We’re Proud Of 
We are proud of creating our first SMS-based service using Twilio API. We are also extremely proud of submitting our very first project to Hackathon. It was a fun experience!

## What We Learned 
Through this project, we got more familiar with a lot of popular APIs like the Twilio and Google Maps Platform. We also learned to use cloud services to host a service.

## What’s Next For PATH FINDER
We believe we could make a more efficient way to find the route by utilizing cache to cut unnecessary API calls. Also, we thought about more options we could add to the service. For example, we can make the service tell our users how filled the upcoming buses are or information about whether the bus drivers are going on a break.

## CODE SHOWCASE
[![PATH FINDER DEMO](http://img.youtube.com/vi/BNNW--CPRdM/0.jpg)](http://www.youtube.com/watch?v=BNNW--CPRdM)

## DEMONSTRATION
[![PATH FINDER DEMO](http://img.youtube.com/vi/f0YUwrMpb_c/0.jpg)](http://www.youtube.com/watch?v=f0YUwrMpb_c)
