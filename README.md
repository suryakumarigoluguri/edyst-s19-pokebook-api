In this repository i have created various pokebook endpoints for users,pokemon posts by different users.
And the user can follow another user 
or 
user can favourite pokemons posted by users

Before running the app.py 
we have to install all the requirements in the requirements.txt file

POST /api/users/login
this end point is to login the user to their account and then token will be generated
 
POST /api/users
to register particular user this endpoint is used

GET /api/user
it will return current user logged in,authentication is required

GET /api/profiles/:username
to get the profile of any user

POST /api/profiles/:username/follow
to follow the any user,authentication is required

GET /api/pokemon
this end point will filter the posts by filtering using tag(or)trainer(or)favourited

GET /api/pokemon/feed
to feed the following users posts

POST /api/pokemon
to create a post,authentication is required

POST /api/pokemon/:name/comments
to comment any post,authentication is required

POST /api/pokemon/:name/favorite
to favourite the posts

GET /api/tags
to list the tags which have given to the posts

Above are some of the end points which to be used in the pokebook-api.
