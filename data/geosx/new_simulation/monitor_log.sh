#!/bin/bash
# Script para monitorear el log de PFLOTRAN en tiempo real

LOG_FILE="pflotran.log"
OUT_FILE="DEP_GAS.out"
TAIL_LINES=50

echo "Monitoreando logs de PFLOTRAN (últimas $TAIL_LINES líneas)"
echo "Presiona Ctrl+C para salir"
echo "================================"

while true; do
    clear
    echo "Última actualización: $(date)"
    echo "================================"
    
    if [ -f "$OUT_FILE" ] && [ -s "$OUT_FILE" ]; then
        echo "=== DEP_GAS.out ==="
        tail -n $TAIL_LINES "$OUT_FILE"
        echo ""
    fi
    
    if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
        echo "=== pflotran.log ==="
        tail -n $TAIL_LINES "$LOG_FILE"
    fi
    
    sleep 2
done

