import { filter, map } from 'lodash';
import { createSelector } from 'reselect';

import { AppState, RouteProps } from '@/js/store';
import { selectEpic, selectEpicSlug } from '@/js/store/epics/selectors';
import { selectProject } from '@/js/store/projects/selectors';

export const selectTaskState = (appState: AppState) => appState.tasks;

export const selectTasksStateByProject = createSelector(
  [selectTaskState, selectProject],
  (tasks, project) => {
    /* istanbul ignore else */
    if (project) {
      return tasks[project.id];
    }
    return undefined;
  },
);

export const selectTasksByProject = createSelector(
  [selectTaskState, selectProject],
  (tasks, project) => {
    /* istanbul ignore else */
    if (project && tasks[project.id]?.fetched === true) {
      return tasks[project.id].tasks;
    }
    return undefined;
  },
);

export const selectTasksByEpic = createSelector(
  [selectTaskState, selectEpic],
  (tasks, epic) => {
    /* istanbul ignore else */
    if (epic && tasks[epic.project]?.fetched) {
      const fetched = tasks[epic.project].fetched;
      if (fetched === true || fetched.includes(epic.id)) {
        return filter(tasks[epic.project].tasks, ['epic.id', epic.id]);
      }
    }
    return undefined;
  },
);

export const selectTaskSlug = (
  appState: AppState,
  { match: { params } }: RouteProps,
) => params.taskSlug;

export const selectTask = createSelector(
  [selectTasksStateByProject, selectEpic, selectEpicSlug, selectTaskSlug],
  (tasks, epic, epicSlug, taskSlug) => {
    if (!tasks || (epicSlug && !epic) || !taskSlug) {
      return undefined;
    }
    const task = tasks.tasks.find(
      (t) => t.slug === taskSlug || t.old_slugs.includes(taskSlug),
    );
    if (task && !(task.epic && task.epic.id !== epic?.id)) {
      return task;
    }
    const notFoundSlug = epic ? `${epic.id}-${taskSlug}` : taskSlug;
    const notFound = tasks.notFound.includes(notFoundSlug);

    return notFound ? null : undefined;
  },
);

export const selectTaskById = (appState: AppState, id?: string | null) =>
  map(appState.tasks, 'tasks')
    .flat()
    .find((t) => t.id === id);
