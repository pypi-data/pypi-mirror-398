import unittest
import pathlib
import datetime

from pytodotxt import Task

from pter.searcher import Searcher
from pter.source import Source
from pter.common import SearchCaseBehaviour


class FakeSource:
    def __init__(self, tasks):
        self.tasks = tasks
        self.filename = pathlib.Path('/tmp/Test.txt')


class SearcherTest(unittest.TestCase):
    def setUp(self):
        self.searcher = Searcher('', SearchCaseBehaviour.INSENSITIVE)

    def search(self, text, tasks):
        self.searcher.text = text
        self.searcher.parse()
        result = []
        source = Source(FakeSource(tasks))
        source.update_contexts_and_projects()
        self.searcher.update_sources([source])
        for task in source.tasks:
            task.todotxt = source
            if self.searcher.match(task):
                result.append(task)
        return result


class TestPhrase(SearcherTest):
    TASKS = [Task("Some phrase id:1"),
             Task("Very different Phrase id:2"),
             Task("Similar phrase id:3"),
             Task("Completely Different id:4 not:")]

    def test_match_one(self):
        results = self.search("different", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2', '4'})

    def test_match_none(self):
        results = self.search("none", self.TASKS)

        self.assertEqual(len(results), 0)

    def test_match_keyword(self):
        results = self.search("id", self.TASKS)

        self.assertEqual(len(results), 4)

    def test_match_id(self):
        results = self.search("id:", self.TASKS)

        self.assertEqual(len(results), 4)

    def test_match_not(self):
        results = self.search("not: e", self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'4',})

    def test_match_not_word(self):
        results = self.search("not:phrase", self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'4',})

    def test_match_some(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search("phrase", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '3'})

    def test_match_case_sensitive(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search("Phrase", self.TASKS)
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2',})

    def test_match_case_insensitive(self):
        results = self.search("Phrase", self.TASKS)
        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '3'})

    def test_match_case_smart(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SMART
        results = self.search("Phrase", self.TASKS)
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2',})


class TestContext(SearcherTest):
    TASKS = [Task("Some @context id:1"),
             Task("Again @context id:2"),
             Task("To be completed @otherwise id:3"),
             Task("Inconsistent @Context id:4")]

    def test_match(self):
        results = self.search("@context", self.TASKS)
        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '4'})

    def test_match_insensitive(self):
        results = self.search("@CONTEXT", self.TASKS)
        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '4'})

    def test_match_case(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search("@context", self.TASKS)
        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_match_case2(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search("@Context", self.TASKS)
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'4',})

    def test_match_case_smart(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SMART
        results = self.search("@Context", self.TASKS)
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'4',})

    def test_match_case_smart2(self):
        tasks = self.TASKS + [Task('@multiple @Contexts id:5'),
                              Task('@context @Multiple id:6')]
        self.searcher.casesensitive = SearchCaseBehaviour.SMART
        results = self.search("@context @Multiple", tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'6',})


class TestProject(SearcherTest):
    TASKS = [Task("Some +project id:1"),
             Task("Again +project id:2"),
             Task("Something +different id:3"),
             Task("Inconsistent +Project id:4")]

    def test_match(self):
        results = self.search("+project", self.TASKS)
        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '4'})

    def test_match_insensitive(self):
        results = self.search("+PROJECT", self.TASKS)
        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '4'})

    def test_match_case(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search("+project", self.TASKS)
        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_match_case2(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search("+Project", self.TASKS)
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'4',})


class TestDue(SearcherTest):
    TASKS = [Task("Soon due:9999-12-31 id:1"),
             Task("Passed due:1900-01-01 id:2"),
             Task("No due date id:3")]

    def test_due(self):
        results = self.search("due:yes", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_no_due(self):
        results = self.search("due:no", self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'3',})

    def test_any_due(self):
        results = self.search("due:any", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_empty_due_search(self):
        today = datetime.datetime.now().strftime(Task.DATE_FMT)
        results = self.search("due:",
                              [Task(f"id:1 Some task due:{today}"),
                               Task("id:2 Some task without due date"),
                               Task("id:3 Another task due:1900-01-01")])

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '3'})

    def test_due_before0(self):
        results = self.search("duebefore:1890-01-01", self.TASKS)
        self.assertEqual(len(results), 0)

    def test_due_before1(self):
        results = self.search("duebefore:2000-01-01", self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2',})

    def test_due_after0(self):
        results = self.search("dueafter:9999-12-31", self.TASKS)
        self.assertEqual(len(results), 0)

    def test_due_after2(self):
        results = self.search("dueafter:1899-12-31", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2',})

    def test_due_between(self):
        results = self.search("dueafter:1899-12-31 duebefore:9999-12-31", self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2',})

    def test_relative_due_after_date(self):
        today = datetime.datetime.now().strftime(Task.DATE_FMT)
        results = self.search("dueafter:yesterday",
                              [Task(f"id:1 Some task due:{today}"),
                               Task("id:2 Some task without due date"),
                               Task("id:3 Another task due:1900-01-01")])

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1',})

    def test_relative_due_date(self):
        today = datetime.datetime.now().strftime(Task.DATE_FMT)
        results = self.search("due:today",
                              [Task(f"id:1 Some task due:{today}"),
                               Task("id:2 Some task without due date"),
                               Task("id:3 Another task due:1900-01-01")])

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1',})

    def test_long_due_match(self):
        today = datetime.datetime.now().strftime(Task.DATE_FMT)
        results = self.search("due:today",
                              [Task(f"id:1 Some task due:{today}T12:00:16"),
                               Task(f"id:2 Due long ago due:1912-01-01T12:00"),
                               Task(f"id:3 Not due")])
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1',})

    def test_long_due_match_after(self):
        today = datetime.datetime.now().strftime(Task.DATE_FMT)
        results = self.search("dueafter:1910-01-01",
                              [Task(f"id:1 Some task due:{today}T12:00:16"),
                               Task(f"id:2 Due long ago due:1912-01-01T12:00"),
                               Task(f"id:3 Not due")])
        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_long_due_match_before(self):
        today = datetime.datetime.now().strftime(Task.DATE_FMT)
        results = self.search("duebefore:today",
                              [Task(f"id:1 Some task due:{today}T12:00:16"),
                               Task(f"id:2 Due long ago due:1912-01-01T12:00"),
                               Task(f"id:3 Not due")])
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2',})


class TestThreshold(SearcherTest):
    TASKS = [Task(f"Threshold in the past id:1 t:{str(datetime.date.today()-datetime.timedelta(days=5))}"),
             Task(f"Threshold in the future id:2 t:{str(datetime.date.today()+datetime.timedelta(days=5))}"),
             Task(f"Threshold today id:3 t:{str(datetime.date.today())}"),
             Task("No threshold id:4")]

    def test_has_t(self):
        results = self.search("t:yes", self.TASKS)

        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '3'})

    def test_no_t(self):
        results = self.search("t:no", self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'4',})

    def test_any_t(self):
        results = self.search("t:any", self.TASKS)

        self.assertEqual(len(results), 4)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '3', '4'})

    def test_visible_now(self):
        results = self.search("", self.TASKS)

        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '3', '4'})

    def test_modified_today1(self):
        """Searching with a t: that's beyond thresholds in the future"""
        then = str(datetime.date.today() + datetime.timedelta(days=6))
        results = self.search(f"t:{then}", self.TASKS)

        self.assertEqual(len(results), 4)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '3', '4'})

    def test_modified_today2(self):
        """Searching with a t: that's in the past"""
        then = str(datetime.date.today() - datetime.timedelta(days=2))
        results = self.search(f"t:{then}", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '4'})

    def test_long_t(self):
        today = datetime.date.today()
        dt1 = (today - datetime.timedelta(days=2)).strftime(Task.DATE_FMT) + "T12:16"
        dt2 = (today + datetime.timedelta(days=3)).strftime(Task.DATE_FMT) + "T02:42:15"
        results = self.search("",
                              [Task(f"Visible id:3 t:{dt1}"),
                               Task(f"Hidden id:6 t:{dt2}"),
                               Task(f"Always id:9 there")
                              ])
        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'3', '9'})


class TestCreated(SearcherTest):
    TASKS = [Task("1900-01-01 A bit older id:1"),
             Task(f"{datetime.datetime.now().strftime(Task.DATE_FMT)} Created today id:2"),
             Task("9876-12-31 I hope there are better tools than pter available by then! id:3"),
             Task("What person wouldn't add a creation date to a task? Right. Me. id:4")]

    def test_relative_created1(self):
        results = self.search("createdbefore:tomorrow", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_relative_created2(self):
        results = self.search("createdafter:-2", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2', '3'})


class TestCompleted(SearcherTest):
    TASKS = [Task("x 2004-12-31 1830-01-01 That took a while id:1"),
             Task("1831-01-01 Another old one id:2"),
             Task("x Task without creation or completion date id:3"),
             Task("x 9999-12-31 2004-12-31 Sure, that's when I finished it id:4")]

    def test_relative1(self):
        results = self.search("completedbefore:today", self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1',})

    def test_only_completed(self):
        results = self.search("done:yes", self.TASKS)

        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '3', '4'})

    def test_only_open(self):
        results = self.search("done:no", self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2',})

    def test_any_completion_status(self):
        results = self.search("done:any", self.TASKS)

        self.assertEqual(len(results), 4)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '3', '4'})


class TestImportance(SearcherTest):
    TASKS = [Task("(A) important and urgent id:1"),
             Task("(B) important id:2"),
             Task("(C) urgent id:3"),
             Task("(D) neither id:4"),
             Task("(b) strange priority id:6"),
             Task("meh! id:5")]

    def test_pri_match(self):
        results = self.search('pri:A', self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attributes.get('id'), ['1'])

    def test_pri_match_case_sensitive(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search('pri:a', self.TASKS)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attributes.get('id'), ['1'])

    def test_no_pri_match(self):
        results = self.search('not:pri:A', self.TASKS)

        self.assertEqual(len(results), 5)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2', '3', '4', '5', '6'})

    def test_less_important(self):
        results = self.search('lessimportant:b', self.TASKS)

        self.assertEqual(len(results), 4)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'3', '4', '5', '6'})

    def test_more_important(self):
        results = self.search('moreimportant:C', self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_importance_range(self):
        results = self.search('mi:d li:a', self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2', '3'})


class TestAfter(SearcherTest):
    def test_show_all(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 after:1')]
        results = self.search('after:', tasks)
        self.assertEqual(len(results), 2)

    def test_hide_after(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 after:1')]
        results = self.search('', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['1'])

    def test_recursion(self):
        tasks = [Task('a id:1 after:3'),
                 Task('b id:2 after:1'),
                 Task('c id:3 after:2')]
        results = self.search('', tasks)
        self.assertEqual(len(results), 0)

    def test_more_parents(self):
        tasks = [Task('a id:1'),
                 Task('b id:2'),
                 Task('c after:1,2')]
        results = self.search('', tasks)
        self.assertEqual(len(results), 2)

        results = self.search('after:1', tasks)
        self.assertEqual(len(results), 1)
        self.assertIn('c', str(results[0]))

    def test_parent_completed(self):
        tasks = [Task('x a id:1'),
                 Task('b after:1 id:test')]
        results = self.search('done:n', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['test'])

    def test_some_parents_completed(self):
        tasks = [Task('x a id:1'),
                 Task('b id:2'),
                 Task('c id:3 after:1,2')]
        results = self.search('done:n', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['2'])

    def test_some_parents_completed2(self):
        tasks = [Task('x a id:1'),
                 Task('b id:2'),
                 Task('c id:3 after:1 after:2')]
        results = self.search('done:n', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['2'])

    def test_all_parents_completed(self):
        tasks = [Task('x a id:1'),
                 Task('x b id:2'),
                 Task('c id:3 after:1,2')]
        results = self.search('done:n', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['3'])

    def test_all_parents_completed2(self):
        tasks = [Task('x a id:1'),
                 Task('x b id:2'),
                 Task('c id:3 after:1 after:2')]
        results = self.search('done:n', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['3'])


class TestIDs(SearcherTest):
    def test_id(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('id:1', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['1'])

    def test_id_not_there(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('id:3', tasks)
        self.assertEqual(len(results), 0)

    def test_ids(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('id:1,2', tasks)
        self.assertEqual(len(results), 2)

    def test_ids2(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('id:1 id:2', tasks)
        self.assertEqual(len(results), 2)

    def test_not_id(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('-id:1', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['2'])

    def test_not_ids(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('-id:1,2', tasks)
        self.assertEqual(len(results), 0)

    def test_not_ids2(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('-id:1 -id:2', tasks)
        self.assertEqual(len(results), 0)

    def test_has_id(self):
        tasks = [Task('a id:1'),
                 Task('b')]
        results = self.search('id:', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['1'])

    def test_has_id_case_insensitive(self):
        tasks = [Task('a id:1'),
                 Task('b')]
        results = self.search('ID:', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['1'])

    def test_has_id_case_sensitive(self):
        tasks = [Task('a id:1'),
                 Task('b')]
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search('ID:', tasks)
        self.assertEqual(len(results), 0)

    def test_has_no_id(self):
        tasks = [Task('a id:1'),
                 Task('b')]
        results = self.search('-id:', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(str(results[0]), 'b')

    def test_has_no_id_case_insensitive(self):
        tasks = [Task('a id:1'),
                 Task('b')]
        results = self.search('-ID:', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(str(results[0]), 'b')

    def test_has_no_id_case_sensitive(self):
        tasks = [Task('a id:1'),
                 Task('b')]
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search('-ID:', tasks)
        self.assertEqual(len(results), 2)

    def test_case_insensitive(self):
        tasks = [Task('a id:t1'),
                 Task('b id:T1')]
        results = self.search('id:t1', tasks)
        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'t1', 'T1'})

    def test_case_insensitive2(self):
        tasks = [Task('a id:t1'),
                 Task('b id:T1')]
        results = self.search('id:T1', tasks)
        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'t1', 'T1'})


class TestRef(SearcherTest):
    def test_ref_not_there(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('ref:2', tasks)
        self.assertEqual(len(results), 0)

    def test_ref_search(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1')]
        results = self.search('ref:1', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['2'])

    def test_after_search(self):
        tasks = [Task('x a id:1'),
                 Task('t id:2 after:1')]
        results = self.search('ref:1', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['2'])

    def test_ref_multiple(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1,4')]
        results = self.search('ref:4', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['2'])

    def test_ref_multiple2(self):
        tasks = [Task('a id:1'),
                 Task('b id:2 ref:1 ref:4')]
        results = self.search('ref:4', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].attr_id, ['2'])

    def test_case_insensitive_ref(self):
        tasks = [Task('a id:t1'),
                 Task('b id:2 ref:t1'),
                 Task('c id:3 ref:T1')]
        results = self.search('ref:T1', tasks)
        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2', '3'})

    def test_case_sensitive_ref(self):
        tasks = [Task('a id:t1'),
                 Task('b id:2 ref:t1'),
                 Task('c id:3 ref:T1')]
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search('ref:T1', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'3',})

    def test_case_smart1(self):
        tasks = [Task('a id:t1'),
                 Task('b id:2 ref:t1'),
                 Task('c id:3 ref:T1')]
        self.searcher.casesensitive = SearchCaseBehaviour.SMART
        results = self.search('ref:T1', tasks)
        self.assertEqual(len(results), 1)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'3',})

    def test_case_smart2(self):
        tasks = [Task('a id:t1'),
                 Task('b id:2 ref:t1'),
                 Task('c id:3 ref:T1')]
        self.searcher.casesensitive = SearchCaseBehaviour.SMART
        results = self.search('ref:t1', tasks)
        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'2', '3',})


class SearchFilename(SearcherTest):
    TASKS = [Task('a id:1')]

    def test_match(self):
        results = self.search('file:test', self.TASKS)
        self.assertEqual(len(results), 1)

    def test_no_match(self):
        results = self.search('file:nope', self.TASKS)
        self.assertEqual(len(results), 0)

    def test_match_not(self):
        results = self.search('not:file:test', self.TASKS)
        self.assertEqual(len(results), 0)

    def test_no_match_not(self):
        results = self.search('not:file:nope', self.TASKS)
        self.assertEqual(len(results), 1)

    def test_case_sensitive_filename(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search('file:test', self.TASKS)
        self.assertEqual(len(results), 0)

    def test_match_case_sensitive_filename(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SENSITIVE
        results = self.search('file:Test', self.TASKS)
        self.assertEqual(len(results), 1)

    def test_match_case_smart_filename(self):
        self.searcher.casesensitive = SearchCaseBehaviour.SMART
        results = self.search('file:Test', self.TASKS)
        self.assertEqual(len(results), 1)


class TestHidden(SearcherTest):
    TASKS = [Task("x 2004-12-31 1830-01-01 That took a while h:1 id:1"),
             Task("1831-01-01 Another old one h:1 id:2"),
             Task("x Task without creation or completion date h:0 id:3"),
             Task("Another one without creation or completion date h:0 id:4"),
             Task("x 9999-12-31 2004-12-31 Sure, that's when I finished it id:5")]

    def test_basic(self):
        results = self.search("", self.TASKS)

        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'3', '4', '5'})

    def test_only_hidden(self):
        results = self.search("h:yes", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_only_hidden_1(self):
        results = self.search("h:1", self.TASKS)

        self.assertEqual(len(results), 2)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2'})

    def test_any_hidden_status(self):
        results = self.search("h:any", self.TASKS)

        self.assertEqual(len(results), 5)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '3', '4', '5'})

    def test_hidden_attribute(self):
        results = self.search("h:", self.TASKS)

        self.assertEqual(len(results), 5)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'1', '2', '3', '4', '5'})

    def test_no_hidden(self):
        results = self.search("h:no", self.TASKS)

        self.assertEqual(len(results), 3)
        self.assertEqual(set(sum([r.attributes['id'] for r in results], start=[])),
                         {'3', '4', '5'})
