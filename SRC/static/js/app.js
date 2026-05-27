document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const addForm = document.getElementById('add-task-form');
    const taskInput = document.getElementById('task-title');
    const tasksList = document.getElementById('tasks-list');
    const totalCount = document.getElementById('total-count');
    const completedCount = document.getElementById('completed-count');
    const completionRate = document.getElementById('completion-rate');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    const refreshBtn = document.getElementById('refresh-btn');

    // Fetch and render tasks
    async function fetchTasks() {
        showLoading(true);
        try {
            const response = await fetch('/api/tasks');
            if (!response.ok) throw new Error('Failed to fetch tasks');
            const tasks = await response.json();
            renderTasks(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
            showError('無法載入任務，請重新整理頁面。');
        } finally {
            showLoading(false);
        }
    }

    // Render task items
    function renderTasks(tasks) {
        tasksList.innerHTML = '';
        
        // Update stats
        const total = tasks.length;
        const completed = tasks.filter(t => t.completed).length;
        const rate = total === 0 ? 0 : Math.round((completed / total) * 100);
        
        totalCount.textContent = total;
        completedCount.textContent = completed;
        completionRate.textContent = `${rate}%`;

        if (total === 0) {
            emptyState.classList.remove('hidden');
            return;
        } else {
            emptyState.classList.add('hidden');
        }

        // Generate list items
        tasks.forEach(task => {
            const li = document.createElement('li');
            li.className = `task-item ${task.completed ? 'completed' : ''}`;
            li.dataset.id = task.id;
            
            li.innerHTML = `
                <div class="task-item-left">
                    <button class="checkbox-container" aria-label="Toggle Complete">
                        <i data-lucide="check"></i>
                    </button>
                    <span class="task-title-text">${escapeHtml(task.title)}</span>
                </div>
                <div class="task-item-actions">
                    <button class="btn-delete" aria-label="Delete Task">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            `;

            // Event listener: Toggle completion
            const checkboxBtn = li.querySelector('.checkbox-container');
            checkboxBtn.addEventListener('click', () => toggleTask(task.id, !task.completed));

            // Event listener: Delete task
            const deleteBtn = li.querySelector('.btn-delete');
            deleteBtn.addEventListener('click', () => deleteTask(task.id, li));

            tasksList.appendChild(li);
        });

        // Initialize newly created lucide icons
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    // Add new task
    addForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = taskInput.value.trim();
        if (!title) return;

        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
            });

            if (!response.ok) throw new Error('Failed to create task');
            
            taskInput.value = '';
            // Refresh tasks list
            await fetchTasks();
        } catch (error) {
            console.error('Error adding task:', error);
            alert('無法新增任務，請稍後再試。');
        }
    });

    // Toggle task completed status
    async function toggleTask(id, completed) {
        try {
            const response = await fetch(`/api/tasks/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ completed })
            });

            if (!response.ok) throw new Error('Failed to update task');
            
            await fetchTasks();
        } catch (error) {
            console.error('Error updating task:', error);
            alert('無法更新任務狀態。');
        }
    }

    // Delete task with animation
    async function deleteTask(id, element) {
        if (!confirm('您確定要刪除此項任務嗎？')) return;

        try {
            const response = await fetch(`/api/tasks/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to delete task');

            // Apply exit animation
            element.classList.add('slide-out');
            
            // Wait for animation to finish before rendering again
            element.addEventListener('animationend', async () => {
                await fetchTasks();
            });
        } catch (error) {
            console.error('Error deleting task:', error);
            alert('無法刪除任務。');
        }
    }

    // Helpers
    function showLoading(show) {
        if (show) {
            loadingState.classList.remove('hidden');
        } else {
            loadingState.classList.add('hidden');
        }
    }

    function showError(msg) {
        tasksList.innerHTML = `<li class="error-msg" style="color: var(--danger); text-align: center; padding: 2rem;">${msg}</li>`;
    }

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;")
                  .replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;")
                  .replace(/"/g, "&quot;")
                  .replace(/'/g, "&#039;");
    }

    // Manual Refresh button
    refreshBtn.addEventListener('click', fetchTasks);

    // Initial load
    fetchTasks();
});
