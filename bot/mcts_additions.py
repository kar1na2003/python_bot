    
    def _run_standard_mcts(self, state: BattleState, team_name: str) -> UserAction:
        """Run standard MCTS with advanced enhancements"""
        root = MCTSNode(state)
        
        # Prioritize actions using killer moves
        if self.use_killer_moves and self.killer_moves:
            root.untried_actions = self.killer_moves.prioritize_actions(
                root.untried_actions, state)
        
        for i in range(self.iterations):
            node = root
            
            # Selection with transposition table check
            while not node.is_terminal() and node.is_fully_expanded():
                # Check transposition table
                if self.use_transposition_table and self.transposition_table:
                    cached = self.transposition_table.lookup(node.state)
                    if cached:
                        visits, value = cached
                        # Use cached value to guide selection
                        pass  # For now, just continue with normal selection
                
                # Select child with best UCB1
                node = max(
                    node.children.values(),
                    key=lambda n: n.ucb1(self.c_constant)
                )
            
            # Expansion
            if not node.is_terminal() and not node.is_fully_expanded():
                action = node.untried_actions.pop()
                next_state = GameSimulator.apply_action(node.state, action)
                child = MCTSNode(next_state, parent=node, action=action)
                node.children[str(action.to_dict())] = child
                node = child
            
            # Simulation (with position evaluation fallback)
            if not node.is_terminal():
                winner = GameSimulator.simulate_random_playout(
                    node.state,
                    max_depth=self.simulation_depth
                )
                reward = 1.0 if winner == team_name else 0.0
                
                # If simulation was truncated, use position evaluation
                if (self.use_position_eval and self.position_eval and 
                    self.simulation_depth and 
                    not node.state.is_game_over):
                    pos_eval = self.position_eval.evaluate_position(node.state, team_name)
                    # Blend simulation and evaluation (70% simulation, 30% evaluation)
                    reward = 0.7 * reward + 0.3 * pos_eval
            else:
                reward = node.reward_for_team(team_name)
            
            # Backpropagation
            backprop_node = node
            while backprop_node is not None:
                backprop_node.visits += 1
                backprop_node.value += reward
                
                # Store in transposition table
                if self.use_transposition_table and self.transposition_table:
                    self.transposition_table.store(
                        backprop_node.state, backprop_node.value, backprop_node.visits)
                
                backprop_node = backprop_node.parent
            
            # Record killer moves
            if self.use_killer_moves and self.killer_moves and node.action:
                self.killer_moves.record_killer_move(state, node.action, reward)
            
            # Early stopping check
            if root.children and i >= 50:
                best_win_rate = max(child.value / child.visits for child in root.children.values())
                if best_win_rate >= self.early_stop_threshold:
                    if self.verbose:
                        print(f"Early stop at iteration {i+1}: win rate {best_win_rate:.2%}")
                    break
            
            if self.verbose and (i + 1) % 100 == 0:
                print(f"MCTS iteration {i + 1}/{self.iterations}")
        
        # Select best child
        if not root.children:
            return UserAction.skip()
        
        best_child = max(root.children.values(), key=lambda n: n.visits)
        
        if self.verbose:
            print(f"Best action selected: {best_child.action.action_type}")
            print(f"  Visits: {best_child.visits}")
            print(f"  Win rate: {best_child.value / best_child.visits:.2%}")
        
        return best_child.action
    
    def _actions_equal(self, action1: UserAction, action2: UserAction) -> bool:
        """Check if two actions are equivalent"""
        if action1.action_type != action2.action_type:
            return False
        
        if action1.action_type == "Move":
            return (hasattr(action1, 'destination') and hasattr(action2, 'destination') and
                    action1.destination == action2.destination)
        elif action1.action_type == "Attack":
            return (hasattr(action1, 'target') and hasattr(action2, 'target') and
                    action1.target == action2.target)
        else:  # Skip
            return True