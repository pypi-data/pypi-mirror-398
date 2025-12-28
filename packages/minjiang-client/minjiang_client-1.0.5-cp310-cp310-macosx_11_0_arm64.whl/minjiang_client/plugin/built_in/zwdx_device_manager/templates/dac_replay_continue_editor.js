(function () {
    'use strict';

    const HARDWARE_CHANNELS = [
        '01_AWGXY1',
        '02_AWGXY2',
        '03_AWGXY3',
        '04_AWGXY4',
        '05_AWGXY5',
        '06_AWGXY6',
        '07_AWGXY7',
        '08_AWGXY8',
        '09_AWGM1',
        '10_AWGM2',
        '11_AWGM3',
        '12_AWGM4',
        '13_AWGZ1',
        '14_AWGZ2',
        '15_AWGZ3',
        '16_AWGZ4',
        '17_AWGZ5',
        '18_AWGZ6',
        '19_AWGZ7',
        '20_AWGZ8'
    ];

    class DacReplayContinueEditor {
        static getDefaultMap() {
            const blank = {};
            HARDWARE_CHANNELS.forEach((key) => {
                blank[key] = false;
            });
            return blank;
        }

        static normalizeMapping(mapping) {
            const normalized = {};
            HARDWARE_CHANNELS.forEach((key) => {
                if (mapping && typeof mapping[key] === 'boolean') {
                    normalized[key] = mapping[key];
                } else {
                    normalized[key] = false;
                }
            });
            return normalized;
        }

        static initEditors(root = document) {
            const wrappers = root.querySelectorAll('.dac-replay-continue-editor');
            wrappers.forEach((wrapper) => {
                if (wrapper.dataset.dacReplayContinueReady === 'true') {
                    return;
                }
                DacReplayContinueEditor.mountEditor(wrapper);
            });
        }

        static mountEditor(wrapper) {
            const hiddenId = wrapper.dataset.targetInput;
            const hiddenInput = document.getElementById(hiddenId);
            if (!hiddenInput) {
                return;
            }
            let mapping = {};
            try {
                mapping = JSON.parse(wrapper.dataset.dacReplayContinue || hiddenInput.value || '{}');
            } catch (err) {
                mapping = {};
            }
            const normalized = DacReplayContinueEditor.normalizeMapping(mapping);

            const table = document.createElement('table');
            table.className = 'dac-replay-continue-table';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>硬件通道</th>
                        <th>启用</th>
                    </tr>
                </thead>
            `;
            const tbody = document.createElement('tbody');

            const updateHiddenValue = () => {
                const serialized = JSON.stringify(normalized);
                hiddenInput.value = serialized;
            };

            HARDWARE_CHANNELS.forEach((hardwareKey) => {
                const currentValue = normalized[hardwareKey];

                const row = document.createElement('tr');
                row.className = 'dac-replay-continue-row';

                const hardwareCell = document.createElement('td');
                hardwareCell.className = 'dac-replay-continue-hw';
                hardwareCell.textContent = hardwareKey;
                row.appendChild(hardwareCell);

                const switchCell = document.createElement('td');
                const switchInput = document.createElement('input');
                switchInput.type = 'checkbox';
                switchInput.className = 'dac-replay-continue-switch';
                switchInput.checked = currentValue === true;
                switchCell.appendChild(switchInput);
                row.appendChild(switchCell);

                const handleChange = () => {
                    normalized[hardwareKey] = switchInput.checked;
                    updateHiddenValue();
                };

                switchInput.addEventListener('change', handleChange);

                tbody.appendChild(row);
            });

            table.appendChild(tbody);

            const tableWrapper = document.createElement('div');
            tableWrapper.className = 'dac-replay-continue-table-wrapper';
            tableWrapper.appendChild(table);

            wrapper.insertBefore(tableWrapper, hiddenInput);
            wrapper.dataset.dacReplayContinueReady = 'true';
            updateHiddenValue();
        }
    }

    window.DacReplayContinueEditor = DacReplayContinueEditor;
})();

