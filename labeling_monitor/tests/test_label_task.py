import pytest
from app.repository import FakeLabelTaskRepository, LabelTask, LabellingStatus
import os
from app.labelling_manager import SuperbLabellingManager

@pytest.fixture
def repository():
    return FakeLabelTaskRepository()


def test_현재_라벨링_중인_태스크를_조회한다(repository):
    # given
    task = LabelTask(
        task_id="task-1",
        status=LabellingStatus.INPROGRESS,
        label_url="https://labeling.com/task-1",
        user_id="user-1"
    )
    repository.save_label_task(task)

    # when
    inprogress_tasks = repository.get_label_tasks_by_status(LabellingStatus.INPROGRESS.value)

    # then
    assert len(inprogress_tasks) == 1
    assert inprogress_tasks[0].task_id == "task-1"
    assert inprogress_tasks[0].status == LabellingStatus.INPROGRESS


def test_라벨링_중인_태스크의_상태를_확인한다(repository):
    # given
    task = LabelTask(
        task_id="task-1",
        status=LabellingStatus.INPROGRESS,
        label_url="https://labeling.com/task-1",
        user_id="user-1"
    )
    repository.save_label_task(task)

    # when
    found_task = repository.get_label_task("task-1")

    # then
    assert found_task is not None
    assert found_task.status == LabellingStatus.INPROGRESS


def test_라벨링_중인_태스크의_상태가_완료되면_데이터를_다운로드한다(repository):
    # given
    task = LabelTask(
        task_id="task-1",
        status=LabellingStatus.INPROGRESS,
        label_url="https://labeling.com/task-1",
        user_id="user-1"
    )
    repository.save_label_task(task)

    # when
    task.status = LabellingStatus.COMPLETE
    updated_task = repository.save_label_task(task)

    # then
    assert updated_task.status == LabellingStatus.COMPLETE
    completed_tasks = repository.get_label_tasks_by_status(LabellingStatus.COMPLETE.value)
    assert len(completed_tasks) == 1
    assert completed_tasks[0].task_id == "task-1"


def test_라벨링_중인_태스크의_상태가_완료되면_학습_트리거를_발행한다(repository):
    # given
    task = LabelTask(
        task_id="task-1",
        status=LabellingStatus.INPROGRESS,
        label_url="https://labeling.com/task-1",
        user_id="user-1"
    )
    repository.save_label_task(task)

    # when
    task.status = LabellingStatus.COMPLETE
    updated_task = repository.save_label_task(task)

    # then
    assert updated_task.status == LabellingStatus.COMPLETE
    # TODO: 학습 트리거 발행 로직 구현 후 테스트 추가


def test_슈퍼브AI에서_완료된_라벨을_다운로드한다():

    # given: 슈퍼브AI에 {task_id}로 이미지를 업로드한다.
    superb_labelling_manager = SuperbLabellingManager(
        project_name='actverse_preview_dev',
        team_name='actnova',
        superbai_token='Bj9hCFmhLkaPS6jQqXTmR2WtOVhPCVLJ2vHyAJ83'
    )

    print('superb client project: ', superb_labelling_manager.client._project)
    print('labeling status: ', superb_labelling_manager.get_labelling_status("sample"))
    # superb_labelling_manager.upload_images("test_data/sample", "sample")

    # when: 라벨링 완료 후 라벨링 내보내기를 요청한다.

    label_data_path = superb_labelling_manager.download_labels("sample", "test_data/sample")

    # then: 라벨링 내보내기 완료 후 라벨링 내보내기 결과를 확인한다.
    # assert label_data_path is not None