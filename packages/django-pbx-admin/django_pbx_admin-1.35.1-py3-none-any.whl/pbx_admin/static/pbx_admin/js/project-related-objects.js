async function renderRelatedObjectsDropdown(projectId, dropdown) {
  const container = document.createElement("div");
  const data = await fetchData(projectId);
  const projParamsData = getProjParamsData(data);
  container.appendChild(createProjParamsContainer("Project Param", projParamsData));
  container.appendChild(createProjSaveParamsContainer(data["project_save"], projectId));
  dropdown.appendChild(container);
  setDropdownWidth(dropdown);
}

function createProjParamsContainer(title, projParamsData) {
  const container = document.createElement("div");
  container.className = "params-container";
  container.appendChild(createTable("Project Param", projParamsData));
  return container;
}

function createProjSaveParamsContainer(data, projectId) {
  const container = document.createElement("div");
  for (const [i, pspData] of Object.entries(data)) {
    container.appendChild(createPspHeader(i));
    container.appendChild(createPspTables(pspData));
  }
  return container;
}

function createPspTables(pspData) {
  const container = document.createElement("div");
  container.className = "accordion-content";
  container.appendChild(createTable("Attribute", pspData["attribute_values"]));
  container.appendChild(createTable("Param", pspData["params"]));
  return container;
}

function createPspHeader(i) {
  const header = document.createElement("h3");
  header.classList.add("text-center", "accordion-header");
  header.innerText = `Project Parameters Set #${parseInt(i) + 1}`;
  return header;
}

function createTable(title, data) {
  const table = document.createElement("table");
  table.className = "proj-related-objs-table";
  const thead = createTableHead(title);
  const tbody = createTableBody(data);
  table.appendChild(thead);
  table.appendChild(tbody);
  return table;
}

function createTableHead(title) {
  const thead = document.createElement("thead");
  const row = document.createElement("tr");
  const col1 = document.createElement("th");
  const col2 = document.createElement("th");

  col1.innerText = title;
  col2.innerText = "Value";

  row.appendChild(col1);
  row.appendChild(col2);
  thead.appendChild(row);
  return thead;
}

function createTableBody(data) {
  const tbody = document.createElement("tbody");
  for (const [key, param] of Object.entries(data)) {
    if (!param) continue;

    const row = document.createElement("tr");
    const col1 = document.createElement("td");
    const col2 = document.createElement("td");

    col1.innerHTML = `<a href=${param["list_url"]} target="_blank">${param["type"]}</a>`;
    col2.innerHTML = `<a href=${param["url"]} target="_blank">${param["name"]}</a>`;

    row.appendChild(col1);
    row.appendChild(col2);
    tbody.appendChild(row)
  }
  return tbody;
}

function getProjParamsData(data) {
  const projParamsData = {...data, ...data["producers"]}
  delete projParamsData["producers"];
  delete projParamsData["project_save"];
  return projParamsData;
}

function clearDropdown(dropdown) {
  dropdown.classList.remove("show");
  dropdown.innerHTML = "";
  dropdown.style.width = "0";
}

function setDropdownWidth(dropdown) {
  const columnsWidth = $.map($("table.proj-related-objs-table th"), function (val) {
    return $(val).width();
  });
  const dropdownWidth = Math.max(...columnsWidth) * 3.3;
  dropdown.style.width = `${dropdownWidth}px`;
}

async function fetchData(projectId) {
  const apiSettings = {
    method: "GET",
    headers: {
      "X-Version": "v1",
    }
  };
  try {
    const response = await fetch(`/api/internal/project-related-objects/${projectId}/`, apiSettings);
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error("Request failed.");
    }
  } catch (error) {
    console.log(error);
  }
}

function accordion() {
  const accordionBtns = document.getElementsByClassName("accordion-header");
  for (let i = 0; i < accordionBtns.length; i++) {
    accordionBtns[i].addEventListener("click", function () {
      const accordionContent = this.nextElementSibling;
      if (accordionContent.style.maxHeight) {
        accordionContent.style.maxHeight = null;
      } else {
        accordionContent.style.maxHeight = accordionContent.scrollHeight + 30 + "px";
        $(".accordion-active").click();
      }
      this.classList.toggle("accordion-active");
      accordionContent.classList.toggle("params-container");
    });
  }
  accordionBtns[0].click();
}

const relatedObjsButton = $(".related-objs-dropdown-btn");


relatedObjsButton.click(async function () {
  const projectId = this.dataset.projectId;
  const dropdown = document.getElementById(`proj-related-objs-dropdown-${projectId}`);
  if (!dropdown.classList.contains("show")) {
    $(".proj-related-objs-dropdown-menu.show").each(function () {
      clearDropdown(this);
    });
    dropdown.classList.add("show");
    await renderRelatedObjectsDropdown(projectId, dropdown);
    accordion();
  } else {
    clearDropdown(dropdown);
  }
});

$(document).mouseup(function (e) {
  const relatedObjsDropdowns = $(".proj-related-objs-dropdown-menu.show");
  const dropdownClicked = relatedObjsDropdowns.is(e.target) || relatedObjsDropdowns.has(e.target).length > 0;
  const buttonClicked = relatedObjsButton.is(e.target) || relatedObjsButton.has(e.target).length > 0;
  if (!dropdownClicked && !buttonClicked) {
    relatedObjsDropdowns.each(function () {
      clearDropdown(this);
    });
  }
});
