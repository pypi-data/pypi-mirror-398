// Copyright (c) 2025 valdaffa. Licensed under the MIT License.
use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;


#[pyfunction]
fn solve_least_cost(
    mut supply: Vec<i32>,
    mut demand: Vec<i32>,
    mut costs: Vec<Vec<i32>>
) -> PyResult<(i32, Vec<Vec<i32>>)> {
    
    // Original dimension for dummy detection
    let orig_rows = supply.len();
    let orig_cols = demand.len();

    // Equalize supply and demand before implementing least cost (May add a dummy row/col)
    equalize_supply_demand(&mut supply, &mut demand, &mut costs);

    let rows: usize = supply.len();
    let cols: usize = demand.len();

    // Identify which index is the dummy using original dimension
    let dummy_row = if rows > orig_rows { Some(rows - 1) } else { None };
    let dummy_col = if cols > orig_cols { Some(cols - 1) } else { None };

    // Empty variables for result (total cost & allocation matrox)
    let mut allocation: Vec<Vec<i32>> = vec![vec![0; cols]; rows];
    let mut total_cost: i32 = 0;

    // Main loop
    // 1. Loop through each cell, find the least cost (other than dummies)
    // 2. Allocate the least cost cell demand
    // 3. Get the next least cost, and allocate again.
    // 4. Rinse and repeat until all non-dummy demand got fulfilled
    // 5. Allocate the dummy
    while supply.iter().sum::<i32>() > 0 && demand.iter().sum::<i32>() > 0 {
        
        // Variables to store least cost cell
        let mut min_val: i32 = i32::MAX;
        let mut target_row: usize = usize::MAX; 
        let mut target_col: usize = usize::MAX;

        // Loop through each cell
        for i in 0..rows {
            for j in 0..cols {
                // If this is a dummy cell, skip it for now
                if dummy_row == Some(i) || dummy_col == Some(j) {
                    continue;
                }

                if supply[i] > 0 && demand[j] > 0 {
                    if costs[i][j] < min_val {
                        min_val = costs[i][j];
                        target_row = i;
                        target_col = j;
                    }
                }
            }
        }

        // If no real cells found, search Dummies ---
        // This runs if we are forced to use the dummy (or if only dummies remain)
        if target_row == usize::MAX {
            for i in 0..rows {
                for j in 0..cols {
                    // We only care about dummies here
                    if dummy_row == Some(i) || dummy_col == Some(j) {
                        if supply[i] > 0 && demand[j] > 0 {
                            if costs[i][j] < min_val {
                                min_val = costs[i][j];
                                target_row = i;
                                target_col = j;
                            }
                        }
                    }
                }
            }
        }

        // Allocation
        if target_row != usize::MAX && target_col != usize::MAX {
            // Get quantity based on which one of supply or demand is lower
            let quantity = std::cmp::min(supply[target_row], demand[target_col]);

            allocation[target_row][target_col] = quantity;

            // Add allocation cost to total_cost
            total_cost += quantity * costs[target_row][target_col];

            supply[target_row] -= quantity;
            demand[target_col] -= quantity;
        } else {
            break; 
        }
    }

    // Final check if all supply is allocated and all demand is fullfilled
    if supply.iter().sum::<i32>() == 0 && demand.iter().sum::<i32>() == 0 {
        Ok((total_cost, allocation))
    } // Else return an error to python
    else {
        Err(PyValueError::new_err("Logic Error: Final Supply and Demand is not 0"))
    }
}


#[pyfunction]
fn solve_vam(
    mut supply: Vec<i32>,
    mut demand: Vec<i32>,
    mut costs: Vec<Vec<i32>>
) -> PyResult<(i32, Vec<Vec<i32>>)> {
    // Equalize supply and demand before implementing VAM
    equalize_supply_demand(&mut supply, &mut demand, &mut costs);

    let rows: usize = supply.len();
    let cols: usize = demand.len();

    // Empty variables for result (total cost & allocation matrix)
    let mut allocation: Vec<Vec<i32>> = vec![vec![0; cols]; rows];
    let mut total_cost: i32 = 0;

    // Main loop
    // 1. Calculate penalty difference for all rows (Row Diff)
    // 2. Calculate penalty difference for all columns (Col Diff)
    // 3. Find the highest difference among all rows and columns
    // 4. Allocate to the cell with the lowest cost in that row/column
    // 5. Rinse and repeat untill all demand/supply is fulfilled
    while supply.iter().sum::<i32>() > 0 && demand.iter().sum::<i32>() > 0 {
        let mut row_diff: Vec<i32> = vec![-1; rows]; // Initialize with -1
        let mut row_min_coord: Vec<Vec<usize>> = vec![vec![usize::MAX, usize::MAX]; rows];

        let mut col_diff: Vec<i32> = vec![-1; cols];
        let mut col_min_coord: Vec<Vec<usize>> = vec![vec![usize::MAX, usize::MAX]; cols];

        for i in 0..rows {
            if supply[i] > 0 {
                let mut min_a: i32 = i32::MAX;
                let mut min_b: i32 = i32::MAX;
                let mut valid_count = 0; // Count valid cells

                for j in 0..cols {
                    if demand[j] > 0 {
                        valid_count += 1;
                        let cost = costs[i][j];

                        if cost < min_a {
                            // Found new lowest value
                            // Old lowest value become 2nd lowest
                            min_b = min_a; 
                            min_a = cost;
                            row_min_coord[i] = vec![i, j];
                        } else if cost < min_b {
                            // Found new 2nd lowest
                            min_b = cost;
                        }
                    }
                }

                // Special handling to avoid math overflow
                if valid_count >= 2 {
                    row_diff[i] = min_b - min_a;
                } else if valid_count == 1 {
                    // If only 1 remains, give it high priority (the cost itself)
                    row_diff[i] = min_a; 
                }
            }
        }

        // Calculate col diff
        for j in 0..cols {
            if demand[j] > 0 {
                let mut min_a: i32 = i32::MAX;
                let mut min_b: i32 = i32::MAX;
                let mut valid_count = 0;

                for i in 0..rows {
                    if supply[i] > 0 {
                        valid_count += 1;
                        let cost = costs[i][j];

                        if cost < min_a {
                            min_b = min_a;
                            min_a = cost;
                            col_min_coord[j] = vec![i, j];
                        } else if cost < min_b {
                            min_b = cost;
                        }
                    }
                }

                if valid_count >= 2 {
                    col_diff[j] = min_b - min_a;
                } else if valid_count == 1 {
                    col_diff[j] = min_a;
                }
            }
        }

        // Find highest diff
        let mut highest_diff: i32 = -1;
        let mut target_row: usize = usize::MAX;
        let mut target_col: usize = usize::MAX;

        for i in 0..rows {
            // Check if this row is valid (diff != -1)
            if row_diff[i] > highest_diff {
                highest_diff = row_diff[i];
                // Safety check index array
                if row_min_coord[i][0] != usize::MAX {
                    target_row = row_min_coord[i][0];
                    target_col = row_min_coord[i][1];
                }
            }
        }

        for j in 0..cols {
            if col_diff[j] > highest_diff {
                highest_diff = col_diff[j];
                if col_min_coord[j][0] != usize::MAX {
                    target_row = col_min_coord[j][0];
                    target_col = col_min_coord[j][1];
                }
            }
        }

        // Allocation
        if target_row != usize::MAX && target_col != usize::MAX {
            // Get quantity based on which one of supply or demand is lower
            let quantity = std::cmp::min(supply[target_row], demand[target_col]);

            // Use += (not =) for safety if cell is visited again (rare in VAM but best practice)
            allocation[target_row][target_col] += quantity;
            total_cost += quantity * costs[target_row][target_col];

            supply[target_row] -= quantity;
            demand[target_col] -= quantity;
        } else {
            // Failsafe: If VAM gets stuck (only remainders left), do manual fill
            // This prevents infinite loop
            let mut found = false;
            for i in 0..rows {
                for j in 0..cols {
                    if supply[i] > 0 && demand[j] > 0 {
                        let quantity = std::cmp::min(supply[i], demand[j]);
                        allocation[i][j] += quantity;
                        total_cost += quantity * costs[i][j];
                        supply[i] -= quantity;
                        demand[j] -= quantity;
                        found = true;
                        break;
                    }
                }
                if found { break; }
            }
            if !found { break; } 
        }
    }

    // Final check if all supply is allocated and all demand is fulfilled
    if supply.iter().sum::<i32>() == 0 && demand.iter().sum::<i32>() == 0 {
        Ok((total_cost, allocation))
    } // Else return an error to python
    else {
        Err(PyValueError::new_err("Logic Error: Supply dan Demand akhir belum 0"))
    }
}

#[pyfunction]
fn solve_nwcr(
    mut supply: Vec<i32>,
    mut demand: Vec<i32>,
    mut costs: Vec<Vec<i32>>
) -> PyResult<(i32, Vec<Vec<i32>>)> {

    // Equalize supply and demand before implementing nwcr
    equalize_supply_demand(&mut supply, &mut demand, &mut costs);

    // Get matrix dimension
    let rows: usize = supply.len();
    let cols: usize = demand.len();

    // Empty variables for result (total cost, allocation matrix)
    let mut allocation: Vec<Vec<i32>> = vec![vec![0; cols]; rows];
    let mut total_cost: i32 = 0;

    // Main loop
    // 1. Loop through the cost matrix start from (0, 0) / northwest
    // 2. Allocate based on supply and demand value
    // 3. If supply exhausted, get to the next row
    // 4. If demand fulfilled, get to the next column and next row
    for i in 0..rows {
        for j in 0..cols {
            if supply[i] > 0 && demand[j] > 0 {
                // Get quantity based on which of supply or demand is lower
                let quantity = std::cmp::min(supply[i], demand[j]);

                // Allocation
                allocation[i][j] = quantity;

                // Add allocation cost to total_cost 
                total_cost += allocation[i][j] * costs[i][j];

                supply[i] -= quantity;
                demand[j] -= quantity;
            }
        }
    }

    // Final check if all supply is allocated and all demand is fullfilled
    if supply.iter().sum::<i32>() == 0 && demand.iter().sum::<i32>() == 0 {
        return Ok((total_cost, allocation))
    } // Else return error to python
    else {
        return Err(PyValueError::new_err("Supply dan Demand akhir belum 0"))
    }
}


#[pyfunction]
fn optimize_modi(
    mut supply: Vec<i32>,
    mut demand: Vec<i32>,
    mut costs: Vec<Vec<i32>>,
    mut allocation: Vec<Vec<i32>>
) -> PyResult<(i32, Vec<Vec<i32>>)> {
    
    // Equalize supply and demand before optimization just to make sure
    equalize_supply_demand(&mut supply, &mut demand, &mut costs);
    
    
    let target_rows = costs.len();
    let target_cols = costs[0].len();

    while allocation.len() < target_rows { allocation.push(vec![0; target_cols]); }
    for row in allocation.iter_mut() { while row.len() < target_cols { row.push(0); } }

    let rows = supply.len();
    let cols = demand.len();
    let mut iteration = 0;

    // 1. Initialize is_basic ONCE
    let mut is_basic = resolve_degeneracy(rows, cols, &allocation); 

    loop {
        // Check degeneracy (just in case we lost count, though manual update is safer)
        // Better: Ensure we maintain exactly m+n-1 true values in is_basic manually below.
        
        // ... Calculate Entering Var ...
        let entering_cell = get_modi_entering_variable(rows, cols, &costs, &is_basic);

        match entering_cell {
            None => break, // Optimal
            Some((start_r, start_c)) => {
                // ... Find Path ...
                let path = get_closed_path(start_r, start_c, rows, cols, &is_basic);
                if path.is_empty() { break; } // Should not happen if degeneracy is handled right

                // ... Find amount_to_move ...
                let mut amount_to_move = i32::MAX;
                let mut leaving_candidate = None;

                // CHECK ONLY (-) NODES FOR LEAVING VARIABLE
                for k in (1..path.len()).step_by(2) {
                    let (r, c) = path[k];
                    if allocation[r][c] < amount_to_move {
                        amount_to_move = allocation[r][c];
                        leaving_candidate = Some((r, c));
                    }
                }

                // Apply Changes
                for (k, &(r, c)) in path.iter().enumerate() {
                    if k % 2 == 0 {
                        allocation[r][c] += amount_to_move;
                    } else {
                        allocation[r][c] -= amount_to_move;
                    }
                }

                // UPDATE BASIS (CRITICAL FIX)
                // 1. Enter the new cell
                is_basic[start_r][start_c] = true; 
                
                // 2. Remove the leaving cell
                // Note: If amount_to_move is 0, we still swap the basis!
                if let Some((lr, lc)) = leaving_candidate {
                    is_basic[lr][lc] = false;
                }
            }
        }
    }

    // Final Cost Calculation
    let mut final_cost = 0;
    for i in 0..rows {
        for j in 0..cols {
            final_cost += allocation[i][j] * costs[i][j];
        }
    }

    Ok((final_cost, allocation))
}


// HELPER MODI: Calculate U & V (Entering Var)
fn get_modi_entering_variable(
    rows: usize, 
    cols: usize, 
    costs: &Vec<Vec<i32>>, 
    is_basic: &Vec<Vec<bool>>
) -> Option<(usize, usize)> {
    
    let mut u: Vec<Option<i32>> = vec![None; rows];
    let mut v: Vec<Option<i32>> = vec![None; cols];
    
    // Assumption: u[0] = 0
    u[0] = Some(0);

    // Calculate U and V potentials
    // Loop enough times to propagate values across the graph
    for _ in 0..(rows + cols) { 
        let mut changed = false;
        for r in 0..rows {
            for c in 0..cols {
                if is_basic[r][c] { 
                    if let Some(ur) = u[r] {
                        if v[c].is_none() {
                            v[c] = Some(costs[r][c] - ur);
                            changed = true;
                        }
                    } else if let Some(vc) = v[c] {
                        if u[r].is_none() {
                            u[r] = Some(costs[r][c] - vc);
                            changed = true;
                        }
                    }
                }
            }
        }
        if !changed { break; }
    }

    // Safety fallback for U/V (should rarely hit if degeneracy is fixed)
    for i in 0..rows { if u[i].is_none() { u[i] = Some(0); } }
    for j in 0..cols { if v[j].is_none() { v[j] = Some(0); } }

    // Find Entering Variable (Most Negative Delta)
    let mut most_negative = 0;
    let mut target_cell = None;

    for r in 0..rows {
        for c in 0..cols {
            // Candidate must be Non-Basic
            if !is_basic[r][c] { 
                let cost_eval = costs[r][c] - (u[r].unwrap() + v[c].unwrap());
                if cost_eval < most_negative {
                    most_negative = cost_eval;
                    target_cell = Some((r, c));
                }
            }
        }
    }

    target_cell
}


// HELPER MODI: Find Loop (DFS)
fn get_closed_path(
    start_r: usize,
    start_c: usize,
    rows: usize,
    cols: usize,
    is_basic: &Vec<Vec<bool>>
) -> Vec<(usize, usize)> {
    
    // Stack stores: (row, col, path_history)
    let mut stack: Vec<(usize, usize, Vec<(usize, usize)>)> = Vec::new();
    
    // Start horizontal
    stack.push((start_r, start_c, vec![(start_r, start_c)]));

    while let Some((curr_r, curr_c, path)) = stack.pop() {
        
        // Check if loop is closed
        if path.len() >= 4 {
            let (first_r, first_c) = path[0];
            let (last_r, last_c) = path[path.len() - 1];
            
            // Valid loop condition
            if last_c == first_c && last_r != first_r {
                 return path; 
            }
        }

        // Determine direction
        // Even length (0, 2..) = Just moved Vertical -> Next is Horizontal
        // Odd length (1, 3..) = Just moved Horizontal -> Next is Vertical
        let is_moving_horizontal = path.len() % 2 != 0; 

        if is_moving_horizontal {
            // Search ROW
            for c in 0..cols {
                if c != curr_c {
                    // KValid if Basic OR it's the start node
                    if is_basic[curr_r][c] || (curr_r == start_r && c == start_c && path.len() > 1) {
                        let mut new_path = path.clone();
                        new_path.push((curr_r, c));
                        stack.push((curr_r, c, new_path));
                    }
                }
            }
        } else {
            // Search COLUMN
            for r in 0..rows {
                if r != curr_r {
                    // Valid if Basic OR it's the start node
                    if is_basic[r][curr_c] || (r == start_r && curr_c == start_c && path.len() > 1) {
                         let mut new_path = path.clone();
                         new_path.push((r, curr_c));
                         stack.push((r, curr_c, new_path));
                    }
                }
            }
        }
    }
    Vec::new() 
}

fn resolve_degeneracy(
    rows: usize,
    cols: usize,
    allocation: &Vec<Vec<i32>>
) -> Vec<Vec<bool>> {
    let mut is_basic = vec![vec![false; cols]; rows];
    let mut count = 0;

    // 1. Mark existing allocations as Basic
    for r in 0..rows {
        for c in 0..cols {
            if allocation[r][c] > 0 {
                is_basic[r][c] = true;
                count += 1;
            }
        }
    }

    let required = rows + cols - 1;

    // 2. Fix Degeneracy: Add Basic Cells (phantom 0s) if needed
    // Logic: Find an empty cell that helps connect rows/cols. 
    // Simplified Heuristic: Fill the first available empty cell that 
    // corresponds to a row/col that has no or few basic cells.
    while count < required {
        let mut added = false;
        
        // Scan for a suitable zero-cell to turn into a Basic Cell
        // Ideally, you pick one that doesn't form a loop, but for patching
        // simple degeneracy, filling the lowest cost (or simple index) usually works.
        for r in 0..rows {
            for c in 0..cols {
                if !is_basic[r][c] {
                    // Mark as basic (alloc remains 0, but is_basic = true)
                    is_basic[r][c] = true;
                    count += 1;
                    added = true;
                    break; 
                }
            }
            if added { break; }
        }
        
        // Safety break
        if !added { break; }
    }

    is_basic
}


fn equalize_supply_demand(
    supply: &mut Vec<i32>,
    demand: &mut Vec<i32>,
    costs: &mut Vec<Vec<i32>>
){
    // Equalize the supply and demand
    let mut total_supply: i32 = supply.iter().sum();
    let mut total_demand: i32 = demand.iter().sum();

    // 1. Compare supply and demand
    // 2. Get the difference between the two
    // 3. Make a dummy to cover the difference
    if total_supply > total_demand{
        let mut difference: i32 = total_supply - total_demand;

        // Make demand dummy
        demand.push(difference);

        // Set the dummy cost to 0 (end of each row / last column)
        for row in costs.iter_mut() {
            row.push(0);
        }
    }
    else if total_supply < total_demand{
        let mut difference: i32 = total_demand - total_supply;

        // Make supply dummy
        supply.push(difference);

        // Set the dummy cost to 0 (the last row)
        let cols: usize = demand.len();
        costs.push(vec![0; cols]);
    }
}


/// A Python module implemented in Rust.
#[pymodule]
mod transport_solver {
    use pyo3::prelude::*;

    #[pymodule_export]
    use super::solve_nwcr;

    #[pymodule_export]
    use super::solve_least_cost;

    #[pymodule_export]
    use super::solve_vam;

    #[pymodule_export]
    use super::optimize_modi;
}
