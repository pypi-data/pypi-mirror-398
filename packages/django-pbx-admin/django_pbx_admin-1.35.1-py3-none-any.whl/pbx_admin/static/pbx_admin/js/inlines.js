$(document).ready(function () {
  const $inlineForm = $('.pb-inline-formset').first();
  if (!$inlineForm.length) {
    return
  }
  const $totalFormsInput = $inlineForm.find('[id$=TOTAL_FORMS]');
  $inlineForm.on('click', '#add-button', null, addRow);
  $inlineForm.on('click', '.remove-button', null, removeRow);

  reorderRows();

  const $rows = getRows();
  const $infinityRow = getInfinityRow($rows);
  const infinityRowIndex = parseInt($infinityRow.attr('id').split('-')[1]);

  setInputsReadonly();
  removeDelete();

  function getRows() {
    return $inlineForm.find('[id^=spine]')
  }

  function reorderRows() {
    const $rows = getRows();
    const $newRows = $rows.filter((i, el) => !$(el).find('input[id$=id]').val());
    const $infinityRow = getInfinityRow($rows);
    $newRows.each((i, row) =>
      $(row).insertBefore($infinityRow, null)
    );
  }

  function getInfinityRow($rows) {
    return $rows.filter((i, el) =>
      $(el).find('input[id$=type]').val() === 'infinity'
    ).last();
  }

  function setInputsReadonly() {
    const firstPagesFromInput = $rows.find('input[id$=pages_from]').first();
    const lastPagesToInput = $rows.find('input[id$=pages_to]').last();
    [firstPagesFromInput, lastPagesToInput].forEach(el =>
      $(el).attr('readonly', true)
    );
    lastPagesToInput.attr('placeholder', 'Infinity');
  }

  function removeDelete() {
    const removeButtons = $rows.find('input[id$=DELETE], button.remove-button');
    [removeButtons.first(), removeButtons.last()].forEach(el =>
      $(el).remove()
    );
  }

  function removeRow(event) {
    const id = event.currentTarget.id.split('-').pop();
    $(`#spine-${id}`).remove();
    recalculateRows();
    $totalFormsInput.val(+$totalFormsInput.val() - 1);
  }

  function addRow(event) {
    event.preventDefault();
    const template = $('#empty-form');
    var row = template.clone(true);
    row.removeClass('empty-form')
      .removeClass('hide')
      .attr('id', '');
    row.insertBefore($infinityRow);
    recalculateRows();
    $totalFormsInput.val(+$totalFormsInput.val() + 1);
  }

  function recalculateRows() {
    $inlineForm.find('tbody > tr')
      .not($infinityRow)
      .each((rowIndex, el) => {
      if (rowIndex >= infinityRowIndex) {
        rowIndex += 1;
      }
      $(el).find('button').attr('id', `remove-button-${rowIndex}`);
      $(el).find('input').each((inputIndex, el) => {
        ['name', 'id'].forEach(field => {
          const fieldArray = el[field].split('-');
          fieldArray[fieldArray.length - 2] = rowIndex;
          $(el).attr(field, fieldArray.join('-'));
        });
      });
      if (el.id !== 'empty-form') $(el).attr('id', `spine-${rowIndex}`);
    });
  }

});


