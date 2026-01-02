class LibraryBook:
    def __init__(self,title,author,year_published,genre,is_checked_out):
        self.title=title
        self.author=author
        self.year_published=year_published
        self.genre=genre
        self.is_checked_out=is_checked_out
        
book_1=LibraryBook("The Alchemist","Paulo Coelho"," 2025","Fantasy,","False")
print(book_1.title)
print(book_1.author)
print(book_1.year_published)
print(book_1.genre)
print(book_1.is_checked_out)

book_2=LibraryBook("Betrand","Love book","2026"," Fiction","False")
print(book_2.title)
print(book_2.author)
print(book_2.year_published)
print(book_2.genre)
print(book_2.is_checked_out)