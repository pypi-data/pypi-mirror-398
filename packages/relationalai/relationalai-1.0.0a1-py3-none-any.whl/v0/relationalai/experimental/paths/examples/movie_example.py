from v0.relationalai.semantics import Model, select, define, data, String
import pandas as pd

model = Model("movies", dry_run=False)
Concept, Relationship = model.Concept, model.Relationship

Movie = Concept("Movie")
Person = Concept("Person")
Directed = Concept("Directed")
ActedIn = Concept("ActedIn")


data(pd.read_csv("movies_data/movies.csv")).into(Movie, keys=["id"])
data(pd.read_csv("movies_data/person.csv")).into(Person, keys=["id"])
data(pd.read_csv("movies_data/directed.csv")).into(Directed, keys=["id"])
data(pd.read_csv("movies_data/actedin.csv")).into(ActedIn, keys=["id"])
# data(pd.read_csv("examples/builder/actors.csv")).into(Person, keys=["actor_id"])

# select(Person.name, Movie.title).where(
#     Directed.from_ == Person.id,
#     Directed.to == Movie.id
# ).inspect()

edge = Relationship("edge3 {String} {String} {String}")

define(edge(Person.name, Movie.title, "directed")).where(
    Directed.from_ == Person.id,
    Directed.to == Movie.id
)

define(edge(Person.name, Movie.title, "acted_in")).where(
    ActedIn.from_ == Person.id,
    ActedIn.to == Movie.id
)

a, b, label = String.ref(), String.ref(), String.ref()
select(a, b, label).where(edge(a, b, label)).inspect()




# # define author relationship by matching author_id
# define(Book.author(Author)).where(Author.author_id == Book.author_id)

# # get each book title with its author's name
# select(Book.title, Book.author.author_name).inspect()

# # get each pair of books published n the same year
# b = Book
# b1 = Book.ref()
# b2 = Book.ref()
# where(
#     b.publication_year == b1.publication_year,
#     b.title < b1.title
# ).select(b.title, b1.title).inspect()

# # get each triple of books published in the same year
# where(
#     b.publication_year == b1.publication_year,
#     b1.publication_year == b2.publication_year,
#     b.title < b1.title,
#     b1.title < b2.title
# ).select(b.title, b1.title, b2.title).inspect()

# # create a relationship for the author's published genres
# Author.genres = Relationship("{Author} has published {genres:str*}")
# # the Book.genre isn't necessary in the when, but the current rel
# # backend fails otherwise
# define(Author.genres(Book.genre)).where(Book.author == Author, Book.genre)

# select(Author.author_name, Author.genres).inspect()

# # get each author that has published in the dystopian genre and another genre
# select(Author.author_name).where(
#     Author.genres == "Dystopian",
#     Author.genres.ref() != "Dystopian"
# ).inspect()
