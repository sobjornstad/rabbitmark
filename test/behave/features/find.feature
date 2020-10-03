Feature: Finding existing bookmarks in the CLI
  Scenario: Find bookmarks containing the string "Maud".
    Given the RabbitMark test database is configured
     When we run the command "find -f Maud"
     Then we get one search result
      And the result is named "Maud (Tennyson)".
