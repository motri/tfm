

document.addEventListener('DOMContentLoaded', () => {
    // In‐memory array of step definitions
    const steps = [];
  
    // DOM references
    const stepsContainer = document.getElementById('steps-container');
    const addStepBtn    = document.getElementById('add-step-btn');
    const nextBtn       = document.getElementById('next-btn');
    const form          = document.getElementById('workflow-form');
    const hiddenInput   = document.getElementById('workflow-json');
  
    // Render the current steps[] as cards
    function renderSteps() {
      stepsContainer.innerHTML = '';
      steps.forEach((step, idx) => {
        const card = document.createElement('div');
        card.className = 'card mb-2 step-card';
        card.dataset.idx = idx;
  
        if (!step.type) {
          card.innerHTML = `
            <div class="card-body">
              <label for="step-type-${idx}">Paso ${idx+1}: elija el tipo type</label>
              <select id="step-type-${idx}" class="form-control step-type-select">
              <option value="">-- elija uno --</option>
              <option value="transfer">Transferir datos al HPC</option>
              <option value="git">Clonar/Obtener de Git</option>
              <option value="slurm">Enviar trabajo SLURM</option>
              </select>
              <button class="btn btn-sm btn-info finish-step mt-2">Agregar</button>
            </div>`;
        } else {
          // Step type already chosen: just show a summary
          card.innerHTML = `
            <div class="card-body">
              <strong>Step ${idx+1}:</strong> ${step.type.toUpperCase()}
            </div>`;
        }
  
        stepsContainer.appendChild(card);
      });
  
      // Enable Next only if at least one step and all have a type
      const allTyped = steps.length > 0 && steps.every(s => !!s.type);
      nextBtn.disabled = !allTyped;
    }
  

    // Add a new blank step
    addStepBtn.addEventListener('click', () => {
      steps.push({ type: null, params: {} });
      renderSteps();
    });
  
    // Delegate click for Finish buttons
    stepsContainer.addEventListener('click', e => {
      if (e.target.matches('.finish-step')) {
        const card = e.target.closest('.step-card');
        const idx  = Number(card.dataset.idx);
        const select = card.querySelector('.step-type-select');
        if (select.value) {
          steps[idx].type = select.value;
          renderSteps();
        } else {
          alert('Please select a step type before finishing.');
        }
      }
    });
  
    // On Next: serialize steps[] into hidden input and submit form
    nextBtn.addEventListener('click', () => {
      hiddenInput.value = JSON.stringify(steps.map(s => ({ type: s.type })));
      form.submit();
    });
  
    // Initial render
    renderSteps();
  });
  